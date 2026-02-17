
import os
import asyncio
import nest_asyncio
import edge_tts
from moviepy.editor import TextClip, AudioFileClip, CompositeVideoClip, ColorClip, concatenate_videoclips, ImageClip
from server.core.llm import LLMService
from PIL import Image, ImageDraw, ImageFont
import textwrap
import random

# Patch for nested asyncio loops (needed for edge-tts in some envs)
nest_asyncio.apply()

class MediaAgent:
    def __init__(self):
        self.llm = LLMService()
        self.output_dir = os.path.join(os.getcwd(), "client", "static", "videos")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _create_text_image(self, text, output_path, size=(1280, 720)):
        # Create gradient background
        width, height = size
        img = Image.new('RGB', size, color='black')
        draw = ImageDraw.Draw(img)
        
        # Simple gradient effect (vertical)
        top_color = (random.randint(0, 50), random.randint(0, 50), random.randint(50, 150))
        bottom_color = (random.randint(0, 30), random.randint(0, 30), random.randint(20, 80))
        
        for y in range(height):
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * y / height)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * y / height)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        # Draw text
        try:
            # Try to load a nice font, fallback to default
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        # Wrap text
        lines = textwrap.wrap(text, width=50) # Adjust width based on font size roughly
        
        # Calculate text height to center it
        text_height = 0
        line_spacing = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_height += bbox[3] - bbox[1] + line_spacing
            
        current_y = (height - text_height) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            
            # Draw shadow/outline for readability
            shadow_offset = 2
            draw.text((x+shadow_offset, current_y+shadow_offset), line, font=font, fill='black')
            draw.text((x, current_y), line, font=font, fill='white')
            
            current_y += bbox[3] - bbox[1] + line_spacing
            
        img.save(output_path)


    async def generate_video(self, topic: str, content_markdown: str) -> str:
        """
        Generates a video summary for the given content.
        Returns the relative path to the generated video.
        """
        print(f"DEBUG: Starting video generation for {topic}")
        
        # 1. Generate Script
        script = self._generate_script(content_markdown)
        if not script:
            raise Exception("Failed to generate video script")
            
        print(f"DEBUG: Script generated. Type: {type(script)}")
        import json
        try:
            print(f"DEBUG: Script preview: {json.dumps(script)[:500]}")
        except:
             print(f"DEBUG: Script preview (raw): {script}")

        # Ensure script is a list
        if isinstance(script, dict):
             # Handle case where LLM returns {"script": [...]} or similar
             if "script" in script and isinstance(script["script"], list):
                 script = script["script"]
             elif "segments" in script and isinstance(script["segments"], list):
                 script = script["segments"]
             else:
                 # Try to find any list value
                 found_list = False
                 for key, val in script.items():
                     if isinstance(val, list):
                         script = val
                         found_list = True
                         break
                 if not found_list:
                     print("DEBUG: Dictionary returned but no list found. Wrapping in list.")
                     script = [script]

        if not isinstance(script, list):
            print("DEBUG: Script is not a list. Wrapping in list.")
            script = [script]
            
        print(f"DEBUG: Processing {len(script)} segments")
        
        # 2. Generate Audio and Clips
        clips = []
        try:
            for idx, segment in enumerate(script):
                print(f"DEBUG: Processing segment {idx+1}/{len(script)}")
                text = ""
                if isinstance(segment, str):
                    text = segment
                elif isinstance(segment, dict):
                    text = segment.get('text', '')
                    if not text:
                         # Try other common keys
                         text = segment.get('content', '') or segment.get('narration', '') or segment.get('script', '')
                else:
                    print(f"DEBUG: Unknown segment type: {type(segment)}")
                    continue
                
                if not text:
                    print(f"DEBUG: Empty text for segment {idx}")
                    continue

                print(f"DEBUG: Segment text length: {len(text)}")
                
                # Increase text length limit for visuals since segments might be longer
                display_text = text[:150] + "..." if len(text) > 150 else text
                
                # Audio
                audio_path = os.path.join(self.output_dir, f"temp_{idx}.mp3")
                communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                await communicate.save(audio_path)
                
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration + 0.5 # Add small pause
                
                # Visual (Pillow Image with Text)
                try:
                    # Create image using PIL
                    img_path = os.path.join(self.output_dir, f"frame_{idx}.png")
                    self._create_text_image(display_text, img_path)
                    
                    # Create ImageClip
                    video_clip = ImageClip(img_path).set_duration(duration)
                except Exception as e:
                    print(f"Error creating image clip: {e}. Fallback to black.")
                    video_clip = ColorClip(size=(1280, 720), color=(0,0,0), duration=duration)

                video_clip = video_clip.set_audio(audio_clip)
                clips.append(video_clip)
            
            if not clips:
                raise Exception("No clips were generated! Check script content.")

            # 3. Concatenate and Write
            final_video = concatenate_videoclips(clips)
            filename = f"video_{topic.replace(' ', '_')}_{int(asyncio.get_event_loop().time())}.mp4"
            output_path = os.path.join(self.output_dir, filename)
            
            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            
            # Cleanup temp files
            for idx in range(len(script)):
                try:
                    os.remove(os.path.join(self.output_dir, f"temp_{idx}.mp3"))
                    os.remove(os.path.join(self.output_dir, f"frame_{idx}.png"))
                except:
                    pass
                    
            # Return relative path for frontend
            return f"/static/videos/{filename}"

        except Exception as e:
            error_msg = f"Error in video generation: {e}"
            print(error_msg)
            with open("debug_media.txt", "a") as f:
                f.write(error_msg + "\n")
                import traceback
                f.write(traceback.format_exc() + "\n")
            return None

    def _generate_script(self, content: str):
        prompt = (
            "You are an expert educational content creator. Your task is to produce a comprehensive **5-minute video lecture script** based on the following topic/content.\n"
            "CRITICAL INSTRUCTION: Even if the input content is short or summary-level, you MUST expand upon it, add examples, context, historical background, and deep explanations to reach the 5-minute target (approx. 800-1000 words).\n"
            "Structure the script into 30-50 segments.\n"
            "Return ONLY a JSON array of objects, where each object has a 'text' field.\n"
            "Example: [{'text': 'Welcome to this in-depth lecture on...'}, {'text': 'To truly understand this, we must look at...'}]\n"
        )
        response = self.llm.generate(content[:6000], prompt, json_mode=True)
        if response:
            print(f"DEBUG: LLM Response (first 200 chars): {response[:200]}")
            import json
            try:
                clean_json = response.replace("```json", "").replace("```", "").strip()
                # Find the first '[' and last ']' to handle potential extra text
                start = clean_json.find('[')
                end = clean_json.rfind(']')
                if start != -1 and end != -1:
                     clean_json = clean_json[start:end+1]
                elif clean_json.startswith('{'):
                     # Might be a single object or wrapped in { "script": ... }
                     pass 
                
                return json.loads(clean_json)
            except Exception as e:
                print(f"Failed to parse script JSON: {response[:500]}... Error: {e}")
        return None
