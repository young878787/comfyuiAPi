"""Utility for parsing metadata from AI generated images (SD and ComfyUI)."""

import json
import re
import struct
import io
import zlib
import logging

logger = logging.getLogger(__name__)

def parse_png_chunks_raw(image_bytes: bytes) -> dict:
    """Parse raw PNG chunks to extract tEXt and iTXt fields without external libraries."""
    if image_bytes[:8] != b'\x89PNG\r\n\x1a\n':
        return {}
    
    info = {}
    index = 8
    length_bytes = len(image_bytes)
    
    while index < length_bytes - 12:
        try:
            chunk_len, = struct.unpack('>I', image_bytes[index:index+4])
            chunk_type = image_bytes[index+4:index+8]
            index += 8
            
            chunk_data = image_bytes[index:index+chunk_len]
            index += chunk_len + 4 # skip CRC
            
            if chunk_type == b'tEXt':
                parts = chunk_data.split(b'\0', 1)
                if len(parts) == 2:
                    key = parts[0].decode('latin-1', errors='ignore')
                    val = parts[1].decode('latin-1', errors='ignore')
                    info[key] = val
            elif chunk_type == b'iTXt':
                parts = chunk_data.split(b'\0', 1)
                if len(parts) == 2:
                    key = parts[0].decode('utf-8', errors='ignore')
                    rest = parts[1]
                    if len(rest) >= 2:
                        comp_flag = rest[0]
                        comp_method = rest[1]
                        
                        # Find language tag (null-terminated)
                        rest = rest[2:]
                        parts2 = rest.split(b'\0', 2)
                        if len(parts2) == 3:
                            # lang = parts2[0].decode('utf-8', errors='ignore')
                            # trans_key = parts2[1].decode('utf-8', errors='ignore')
                            text_bytes = parts2[2]
                            
                            if comp_flag == 1 and comp_method == 0:
                                try:
                                    text_bytes = zlib.decompress(text_bytes)
                                except Exception:
                                    pass
                            
                            val = text_bytes.decode('utf-8', errors='ignore')
                            info[key] = val
        except Exception as e:
            logger.debug(f"Error parsing raw PNG chunk: {e}")
            break
            
    return info

def parse_image_metadata(image_bytes: bytes) -> dict:
    """
    Extract AI generation metadata from image bytes.
    Supports Stable Diffusion (A1111) parameters and ComfyUI prompt/workflow metadata.
    """
    result = {
        "format": "unknown",
        "positive_prompt": "",
        "negative_prompt": "",
        "parameters": {}
    }
    
    # Try importing PIL to read metadata, fall back to raw parsing
    info = {}
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        info = img.info
    except Exception as e:
        logger.warning(f"Failed to use PIL for metadata parsing: {e}. Falling back to raw binary parsing.")
        
    # If PIL failed or returned empty info, try raw PNG parsing
    if not info:
        info = parse_png_chunks_raw(image_bytes)
        
    # 1. ComfyUI Format
    if "prompt" in info:
        result["format"] = "comfyui"
        try:
            prompt_json = json.loads(info["prompt"])
            
            positive_texts = []
            negative_texts = []
            sampler_nodes = []
            clip_nodes = {}
            
            for node_id, node in prompt_json.items():
                class_type = node.get("class_type", "")
                if class_type in ("CLIPTextEncode", "SDXLPromptEncoder", "CLIPTextEncodeSDXL", "CLIPTextEncodeSVD"):
                    clip_nodes[node_id] = node
                elif "Sampler" in class_type or class_type == "KSampler" or class_type == "KSamplerAdvanced":
                    sampler_nodes.append(node)
            
            # Trace KSampler connections
            for sampler in sampler_nodes:
                inputs = sampler.get("inputs", {})
                pos_conn = inputs.get("positive")
                neg_conn = inputs.get("negative")
                
                if isinstance(pos_conn, list) and len(pos_conn) > 0:
                    pos_node_id = str(pos_conn[0])
                    if pos_node_id in clip_nodes:
                        text = clip_nodes[pos_node_id].get("inputs", {}).get("text", "")
                        if text and text not in positive_texts:
                            positive_texts.append(text)
                            
                if isinstance(neg_conn, list) and len(neg_conn) > 0:
                    neg_node_id = str(neg_conn[0])
                    if neg_node_id in clip_nodes:
                        text = clip_nodes[neg_node_id].get("inputs", {}).get("text", "")
                        if text and text not in negative_texts:
                            negative_texts.append(text)
            
            # Fallback: if no connections matched, scan all CLIP nodes
            if not positive_texts:
                for node in clip_nodes.values():
                    text = node.get("inputs", {}).get("text", "")
                    if text:
                        text_lower = text.lower()
                        if "worst quality" in text_lower or "low quality" in text_lower or "bad anatomy" in text_lower:
                            negative_texts.append(text)
                        else:
                            positive_texts.append(text)
            
            result["positive_prompt"] = "\n".join(positive_texts)
            result["negative_prompt"] = "\n".join(negative_texts)
            
            # Extract sampler params
            if sampler_nodes:
                s_inputs = sampler_nodes[0].get("inputs", {})
                result["parameters"] = {
                    "steps": s_inputs.get("steps"),
                    "cfg": s_inputs.get("cfg"),
                    "seed": s_inputs.get("seed"),
                    "sampler": s_inputs.get("sampler_name"),
                    "scheduler": s_inputs.get("scheduler")
                }
        except Exception as e:
            logger.error(f"Failed to parse ComfyUI prompt JSON: {e}")
            
    # 2. Stable Diffusion Format
    elif "parameters" in info:
        result["format"] = "stable_diffusion"
        try:
            params_str = info["parameters"]
            parts = params_str.split("\n")
            
            pos_lines = []
            neg_lines = []
            param_line = ""
            
            in_negative = False
            for part in parts:
                part_strip = part.strip()
                if part_strip.startswith("Negative prompt:"):
                    in_negative = True
                    neg_lines.append(part_strip[len("Negative prompt:"):].strip())
                elif any(part_strip.startswith(prefix) for prefix in ["Steps:", "Sampler:", "CFG scale:", "Seed:"]):
                    param_line = part_strip
                    in_negative = False
                else:
                    if in_negative:
                        neg_lines.append(part_strip)
                    else:
                        pos_lines.append(part_strip)
            
            result["positive_prompt"] = "\n".join(pos_lines).strip()
            result["negative_prompt"] = "\n".join(neg_lines).strip()
            
            if param_line:
                # Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 12345, Size: 512x512
                # Match parameters by key-value pairs
                param_matches = re.findall(r'([^:,]+):\s*([^,]+)', param_line)
                params_dict = {}
                for k, v in param_matches:
                    params_dict[k.strip().lower()] = v.strip()
                
                result["parameters"] = {
                    "steps": int(params_dict["steps"]) if "steps" in params_dict else None,
                    "cfg": float(params_dict["cfg scale"]) if "cfg scale" in params_dict else None,
                    "seed": int(params_dict["seed"]) if "seed" in params_dict else None,
                    "sampler": params_dict.get("sampler"),
                }
                
                if "size" in params_dict:
                    size_match = re.match(r'(\d+)x(\d+)', params_dict["size"])
                    if size_match:
                        result["parameters"]["width"] = int(size_match.group(1))
                        result["parameters"]["height"] = int(size_match.group(2))
        except Exception as e:
            logger.error(f"Failed to parse Stable Diffusion parameters: {e}")
            
    return result
