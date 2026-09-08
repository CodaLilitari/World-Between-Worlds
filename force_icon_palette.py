"""Deterministic indexed allocation-icon derivation; contains no game assets.

Native JK inputs: three 28x28 8-bit frames. Source/target palettes are the
actual allocation-menu background palettes, not UIColormap.cmp.
"""
import hashlib
import math
import struct

WEIGHTS=(299,587,114)

def allocation_menu_palette(data):
    """Read the actual embedded allocation-background palette, strictly."""
    if not isinstance(data,bytes) or len(data)<128 or data[:4]!=b'BM  ' or struct.unpack_from('<I',data,4)[0]!=70:
        raise ValueError('Unsupported allocation background bitmap')
    flags,count=struct.unpack_from('<II',data,12)
    if flags&~3 or not flags&2 or not 1<=count<=64 or struct.unpack_from('<I',data,36)[0]!=8:
        raise ValueError('Allocation background requires an embedded 8-bit palette')
    offset=128
    for _ in range(count):
        if offset+8>len(data):raise ValueError('Truncated allocation background frame')
        width,height=struct.unpack_from('<II',data,offset)
        if not 1<=width<=4096 or not 1<=height<=4096:raise ValueError('Invalid allocation background dimensions')
        offset+=8+width*height
        if offset>len(data):raise ValueError('Truncated allocation background pixels')
    palette=data[offset:]
    _palette(palette)
    return palette

def _palette(raw):
    if not isinstance(raw,bytes) or len(raw)!=768:
        raise ValueError('Expected an exact 256-color RGB menu palette')
    return tuple(tuple(raw[i:i+3]) for i in range(0,768,3))

def _parse(data):
    if not isinstance(data,bytes) or len(data)<128 or data[:4]!=b'BM  ' or struct.unpack_from('<I',data,4)[0]!=70:
        raise ValueError('Unsupported allocation bitmap header')
    if struct.unpack_from('<I',data,16)[0]!=3 or struct.unpack_from('<I',data,36)[0]!=8:
        raise ValueError('Expected three original 8-bit allocation frames')
    frames=[]; offset=128
    for _ in range(3):
        if len(data)<offset+792 or struct.unpack_from('<II',data,offset)!=(28,28):
            raise ValueError('Expected complete 28x28 allocation frames')
        frames.append(data[offset:offset+792]);offset+=792
    flags=struct.unpack_from('<I',data,12)[0]
    if flags&~3: raise ValueError('Unsupported allocation palette flags')
    palette=data[offset:]
    if len(palette)!=(768 if flags&2 else 0):
        raise ValueError('Unexpected allocation palette payload')
    key=struct.unpack_from('<I',data,28)[0]
    if key>255: raise ValueError('Invalid indexed allocation color key')
    return frames,palette,flags,key

def _error(left,right):
    return sum(w*(a-b)**2 for w,a,b in zip(WEIGHTS,left,right))

def derive_allocation_icon(data,source_palette,target_palette):
    source=_palette(source_palette);target=_palette(target_palette)
    frames,embedded,flags,key=_parse(data)
    if embedded and embedded!=source_palette:
        raise ValueError('Embedded bitmap and declared source palette disagree')
    # GUI alpha blits skip index0 even for native icons with palFmt=0. Preserve
    # that mask plus any explicit color key, and never create new transparent pixels.
    transparent={0}
    if flags&1:transparent.add(key)
    opaque=[i for i in range(256) if i not in transparent]
    neutral=[i for i in opaque if max(target[i])-min(target[i])<=2]
    if not neutral or min(sum(target[i]) for i in neutral)>3*8 or max(sum(target[i]) for i in neutral)<3*80:
        raise ValueError('Target palette lacks a usable dark neutral ramp')
    mapped=[];disabled=[]
    for i,color in enumerate(source):
        if i in transparent:
            mapped.append(i);disabled.append(i);continue
        # Stable smallest-index tie break. Exact duplicate colors preserve their
        # index when possible, avoiding pointless changes on equal palettes.
        mapped.append(i if target[i]==color and i in opaque else min(opaque,key=lambda j:(_error(color,target[j]),j)))
        # A derived approximation of native MotS's dark neutral disabled style:
        # one third of source luma, quantized into the existing target palette.
        gray=sum(w*c for w,c in zip(WEIGHTS,color))//3000
        disabled.append(min(neutral,key=lambda j:(_error((gray,gray,gray),target[j]),j)))
    normal_map=bytes(mapped);disabled_map=bytes(disabled)
    header=bytearray(data[:128]);struct.pack_into('<III',header,16,4,0,0)
    output_frames=[f[:8]+f[8:].translate(normal_map) for f in frames]
    output_frames.append(frames[0][:8]+frames[0][8:].translate(disabled_map))
    # A source bitmap carrying its own palette must carry the target palette
    # after its pixel indices have been remapped. Native reviewed inputs have none.
    return bytes(header)+b''.join(output_frames)+(target_palette if embedded else b'')

def derivation_report(data,output,source_palette,target_palette):
    expected=derive_allocation_icon(data,source_palette,target_palette)
    if output!=expected:raise ValueError('Output differs from the deterministic derivation')
    source=_palette(source_palette);target=_palette(target_palette)
    frames,embedded,flags,key=_parse(data)
    transparent={0}|({key} if flags&1 else set())
    errors=[];old_errors=[];deltas=[];changed=[];masks=[]
    for n,frame in enumerate(frames):
        out=output[128+792*n+8:128+792*(n+1)]
        changed.append(sum(a!=b for a,b in zip(frame[8:],out)))
        masks.append(all((a in transparent)==(b in transparent) for a,b in zip(frame[8:],out)))
        for a,b in zip(frame[8:],out):
            if a in transparent:continue
            errors.append(_error(source[a],target[b])/1000)
            old_errors.append(_error(source[a],target[a])/1000)
            deltas.append(max(abs(x-y) for x,y in zip(source[a],target[b])))
    disabled=output[128+792*3+8:128+792*4]
    masks.append(all((a in transparent)==(b in transparent) for a,b in zip(frames[0][8:],disabled)))
    return {'method':'source-menu-to-target-menu nearest weighted RGB; disabled one-third source luma into target neutral ramp',
            'input_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(output).hexdigest(),
            'source_palette_sha256':hashlib.sha256(source_palette).hexdigest(),'target_palette_sha256':hashlib.sha256(target_palette).hexdigest(),
            'normal_frame_indices_changed':changed,'transparent_masks_preserved':masks,
            'weighted_rgb_rmse':math.sqrt(sum(errors)/len(errors)) if errors else 0,
            'unremapped_weighted_rgb_rmse':math.sqrt(sum(old_errors)/len(old_errors)) if old_errors else 0,
            'maximum_pixel_weighted_rgb_error':math.sqrt(max(errors)) if errors else 0,
            'maximum_channel_error':max(deltas,default=0),'native_dimensions':[28,28],
            'disabled_palette_indices':sorted(set(disabled)),'embedded_palette_replaced':bool(embedded),
            'rendered_game_ui_verified':False}
