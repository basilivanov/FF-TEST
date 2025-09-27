import os
import io
import json
from google.cloud import vision

# --- CONFIGURATION ---
KEY_PATH = "/opt/feature-factory/data/etl-marketplace-29003bd0ad61.json"
IMAGE_DIR = "/opt/feature-factory/photo_work"
RESULTS_DIR = "/opt/feature-factory/vision_results"

# --- MAPPING LOGIC ---
LABEL_TO_SCENE_MAP = {
    "Massage": "hero_table_setup",
    "Skin": "hands_macro",
    "Hand": "hands_action",
    "Arm": "hands_action",
    "Leg": "hands_action",
    "Textile": "textile_detail",
    "Towel": "textile_detail",
    "Bottle": "still_life_tray",
    "Room": "atmosphere_room_wide",
    "Furniture": "atmosphere_room_wide",
    "Interior design": "atmosphere_room_wide",
    "Closet": "entry_cloakroom",
    "Door": "entry_cloakroom",
    "Locker": "entry_cloakroom",
}

def classify_images_with_vision_api():
    """
    Classifies images and saves the results to individual files.
    """
    print("--- Starting Image Classification with Google Vision API ---")

    # 1. Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print(f"Results will be saved to: {RESULTS_DIR}")

    # 2. Authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    try:
        client = vision.ImageAnnotatorClient()
        print("Successfully authenticated with Google Cloud Vision.")
    except Exception as e:
        print(f"Authentication failed. Please check your key file at '{KEY_PATH}'. Error: {e}")
        return

    # 3. Check for image directory
    if not os.path.isdir(IMAGE_DIR):
        print(f"Error: Image directory not found at '{IMAGE_DIR}'.")
        return

    # 4. Process each image
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print(f"No images found in '{IMAGE_DIR}'.")
        return
        
    print(f"Found {len(image_files)} images to process.")

    for filename in image_files:
        image_path = os.path.join(IMAGE_DIR, filename)
        print(f"--- Processing: {filename} ---")

        with io.open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        features = [
            {"type_": vision.Feature.Type.LABEL_DETECTION, "max_results": 15},
            {"type_": vision.Feature.Type.IMAGE_PROPERTIES, "max_results": 5},
        ]
        request = vision.AnnotateImageRequest(image=image, features=features)
        
        try:
            response = client.annotate_image(request=request)
            if response.error.message:
                print(f"  Error from API: {response.error.message}")
                continue
        except Exception as e:
            print(f"  API call failed: {e}")
            continue

        # 5. Interpret and structure the response
        detected_labels = [{"description": label.description, "score": label.score} for label in response.label_annotations]
        
        scene_tag = "misc_room"
        highest_score = 0.0
        for label in detected_labels:
            if label["description"] in LABEL_TO_SCENE_MAP and label["score"] > highest_score:
                scene_tag = LABEL_TO_SCENE_MAP[label["description"]]
                highest_score = label["score"]

        outfit_guess = "unknown"
        dominant_colors = response.image_properties_annotation.dominant_colors.colors
        color_scores = {"white": 0.0, "navy": 0.0, "beige": 0.0}
        for color_info in dominant_colors:
            color = color_info.color
            score = color_info.pixel_fraction
            if color.red > 200 and color.green > 200 and color.blue > 200: color_scores["white"] += score
            elif color.red < 60 and color.green < 80 and color.blue > 100: color_scores["navy"] += score
            elif 190 < color.red < 240 and 170 < color.green < 220 and 130 < color.blue < 190: color_scores["beige"] += score
        
        if color_scores:
            top_color = max(color_scores, key=color_scores.get)
            if color_scores[top_color] > 0.1: outfit_guess = top_color

        # 6. Save result to a file
        result_data = {
            "source_file": filename,
            "assigned_scene_tag": scene_tag,
            "scene_tag_confidence": highest_score,
            "assigned_outfit_guess": outfit_guess,
            "vision_api_labels": detected_labels,
            "vision_api_colors": [{"red": c.color.red, "green": c.color.green, "blue": c.color.blue, "fraction": c.pixel_fraction} for c in dominant_colors]
        }

        result_filename = os.path.splitext(filename)[0] + ".json"
        result_path = os.path.join(RESULTS_DIR, result_filename)
        
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=4)
        
        print(f"  -> Result saved to {result_filename}")

    print("\n--- Classification Complete ---")

if __name__ == "__main__":
    classify_images_with_vision_api()