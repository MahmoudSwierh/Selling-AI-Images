import os
import pyiqa
import torch
import json
import shutil
from pathlib import Path

# Set threshold for deletion
threshold_score = 4

script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent


# Set the directory containing images
midjourney_dir = base_dir / "midjourney"
processing_dir = base_dir / "Filtering"
output_dir = base_dir / "Scored-To Review"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
iqa_metric = pyiqa.create_metric('musiq', device=device)

for image_file in os.listdir(midjourney_dir):
    old_image_path = os.path.join(midjourney_dir, image_file)
    if os.path.isfile(old_image_path) and image_file.lower().endswith(('png', 'jpg', 'jpeg')):
        new_image_path = os.path.join(processing_dir, image_file)

        shutil.move(old_image_path, new_image_path)

# Iterate through each image in the directory
for image_file in os.listdir(processing_dir):
    image_path = os.path.join(processing_dir, image_file)
    if os.path.isfile(image_path):
        try:
            # Get the aesthetic score for the image
            score = iqa_metric(image_path).item()
            print(f"{image_file}: {score}")

            _, file_extension = os.path.splitext(image_file)
            
            if score >= threshold_score:
                # Construct base filename using score
                base_filename = str(int(score * 100000))
                new_image_path = os.path.join(output_dir, base_filename + file_extension)

                # Add suffix if file already exists to prevent overwriting
                suffix = 1
                while os.path.exists(new_image_path):
                    new_filename = f"{base_filename}{suffix}{file_extension}"
                    new_image_path = os.path.join(output_dir, new_filename)
                    suffix += 1

                shutil.move(image_path, new_image_path)

            else:
                # Delete low-quality images
                print(image_file + " Deleted")
                os.remove(image_path)
        except Exception as e:
            print(f"Error processing {image_file}: {e}")

print("Image filtering completed. High-quality images have been retained and saved.")