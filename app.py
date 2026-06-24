import streamlit as st
import os
import json
from datetime import datetime
from PIL import Image
import numpy as np
import pandas as pd
import cv2
from geopy.distance import geodesic
import folium
from io import BytesIO
import requests

# ============================================================
# EMBEDDED DATA
# ============================================================
PLANT_DISEASES = {
    "maize": {
        "diseases": [
            {"name": "Maize Lethal Necrosis (MLN)", "symptoms": ["yellow streaks on leaves", "dwarfing", "necrotic lesions", "stunted growth"], "causes": ["Viral"], "treatments": [{"type": "cultural", "name": "Remove infected plants", "active_ingredients": ["None"], "trade_names": ["N/A"], "procedure": "1. Uproot infected plants\n2. Burn or bury deeply\n3. Control vectors with insecticide"}], "prevention": "Use certified seed, resistant varieties, crop rotation", "severity": "Critical", "specialist_required": True, "local_names": ["Chilala cha chimanga"]},
            {"name": "Gray Leaf Spot", "symptoms": ["rectangular gray lesions", "leaf blight", "yield reduction"], "causes": ["Cercospora zeae-maydis"], "treatments": [{"type": "chemical", "name": "Mancozeb 80% WP", "active_ingredients": ["Mancozeb"], "trade_names": ["Dithane M-45"], "procedure": "1. Mix 50g per 20L water\n2. Spray every 7-10 days"}], "prevention": "Crop rotation, resistant varieties, proper spacing", "severity": "Moderate", "specialist_required": False, "local_names": ["Mphutsi wa udzu"]},
            {"name": "Fall Armyworm", "symptoms": ["ragged holes in leaves", "frass in whorls", "skeletonized leaves"], "causes": ["Spodoptera frugiperda"], "treatments": [{"type": "chemical", "name": "Emamectin Benzoate", "active_ingredients": ["Emamectin benzoate"], "trade_names": ["Proclaim"], "procedure": "1. Mix 5g per 20L water\n2. Target whorls\n3. Repeat after 7 days"}, {"type": "organic", "name": "Tephrosia extract", "active_ingredients": ["Rotenone"], "trade_names": ["Fish bean"], "procedure": "1. Pound 1kg leaves\n2. Soak in 10L water 24hrs\n3. Strain and spray"}], "prevention": "Early planting, hand picking, pheromone traps", "severity": "Severe", "specialist_required": False, "local_names": ["Mbozi ya chimanga"]}
        ]
    },
    "cassava": {
        "diseases": [
            {"name": "Cassava Mosaic Disease", "symptoms": ["mosaic pattern", "leaf distortion", "stunted growth"], "causes": ["ACMV"], "treatments": [{"type": "cultural", "name": "Use disease-free cuttings", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. Select healthy plants\n2. Hot water treat cuttings (50C, 10min)"}], "prevention": "Resistant varieties, certified cuttings, control whiteflies", "severity": "Severe", "specialist_required": False, "local_names": ["Chilala cha chinangwa"]},
            {"name": "Cassava Brown Streak", "symptoms": ["brown streaks on stems", "root necrosis", "dry rot"], "causes": ["CBSV"], "treatments": [{"type": "cultural", "name": "Plant tolerant varieties", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. Use Narocass 1, Mkumba\n2. Harvest within 9 months"}], "prevention": "Tolerant varieties, early harvest, crop rotation", "severity": "Critical", "specialist_required": True, "local_names": ["Mphutsi wa chinangwa"]}
        ]
    },
    "groundnuts": {
        "diseases": [
            {"name": "Groundnut Rosette Disease", "symptoms": ["chlorotic ring spots", "stunted plants", "bunched leaves", "no pod formation"], "causes": ["Groundnut rosette virus"], "treatments": [{"type": "cultural", "name": "Early planting and close spacing", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. Plant early in season\n2. Use close spacing (30cm x 10cm)\n3. Remove infected plants"}], "prevention": "Plant resistant varieties, early planting, close spacing, control aphids", "severity": "Severe", "specialist_required": False, "local_names": ["Chilala cha mtedza"]},
            {"name": "Early Leaf Spot", "symptoms": ["brown spots with yellow halo", "defoliation", "reduced yield"], "causes": ["Cercospora arachidicola"], "treatments": [{"type": "chemical", "name": "Chlorothalonil 720 g/L SC", "active_ingredients": ["Chlorothalonil"], "trade_names": ["Bravo", "Daconil"], "procedure": "1. Apply when first spots appear\n2. Mix 30ml per 20L water\n3. Spray every 14 days"}], "prevention": "Crop rotation, resistant varieties, proper spacing, remove crop residues", "severity": "Moderate", "specialist_required": False, "local_names": ["Mphutsi wa masamba"]}
        ]
    },
    "tobacco": {
        "diseases": [
            {"name": "Tobacco Mosaic Virus", "symptoms": ["mottled light and dark green", "leaf distortion", "stunted growth", "mosaic pattern"], "causes": ["Tobacco mosaic virus"], "treatments": [{"type": "cultural", "name": "Remove infected plants and sanitize", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. Remove and destroy infected plants\n2. Wash hands with soap before handling healthy plants\n3. Sterilize tools with 10% bleach solution\n4. Do not smoke in tobacco fields"}], "prevention": "Use resistant varieties, sanitize tools and hands, control weeds, avoid smoking near fields", "severity": "Moderate", "specialist_required": False, "local_names": ["Chilala cha fodya"]}
        ]
    },
    "tomatoes": {
        "diseases": [
            {"name": "Tomato Early Blight", "symptoms": ["dark brown spots with concentric rings", "yellowing of lower leaves", "stem lesions", "fruit rot"], "causes": ["Alternaria solani"], "treatments": [{"type": "chemical", "name": "Mancozeb + Metalaxyl", "active_ingredients": ["Mancozeb", "Metalaxyl"], "trade_names": ["Ridomil Gold MZ", "Apron Plus"], "procedure": "1. Mix 50g per 20L water\n2. Apply at first sign of disease\n3. Spray every 7-10 days"}, {"type": "organic", "name": "Baking soda spray", "active_ingredients": ["Sodium bicarbonate"], "trade_names": ["Baking soda"], "procedure": "1. Mix 1 tbsp baking soda + 1 tsp liquid soap per 1L water\n2. Spray on affected leaves\n3. Repeat every 5-7 days"}], "prevention": "Crop rotation, stake plants, remove lower leaves, mulch, avoid overhead irrigation", "severity": "Moderate", "specialist_required": False, "local_names": ["Mphutsi wa matimbi"]}
        ]
    }
}

LIVESTOCK_DISEASES = {
    "cattle": {
        "diseases": [
            {"name": "East Coast Fever", "symptoms": ["swollen lymph nodes", "fever", "difficulty breathing", "anemia"], "causes": ["Theileria parva"], "treatments": [{"type": "chemical", "name": "Buparvaquone", "active_ingredients": ["Buparvaquone"], "trade_names": ["Butalex"], "procedure": "1. 2.5mg/kg IM\n2. Repeat after 48-72hrs"}], "prevention": "Tick control, vaccination, tick-resistant breeds", "severity": "Critical", "specialist_required": True, "local_names": ["Matenda a ng'ombe"], "withdrawal_period": "28 days"},
            {"name": "Foot and Mouth Disease", "symptoms": ["blisters on mouth/feet", "salivation", "lameness", "fever"], "causes": ["FMDV"], "treatments": [{"type": "supportive", "name": "Isolation and supportive care", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. ISOLATE - NOTIFIABLE\n2. Report to authorities\n3. Soft feed, clean wounds"}], "prevention": "Vaccination, movement control, quarantine", "severity": "Critical", "specialist_required": True, "local_names": ["Mphutsi wa miyendo"], "withdrawal_period": "N/A"},
            {"name": "Trypanosomiasis", "symptoms": ["intermittent fever", "anemia", "edema under jaw", "weight loss"], "causes": ["Trypanosoma"], "treatments": [{"type": "chemical", "name": "Diminazene", "active_ingredients": ["Diminazene aceturate"], "trade_names": ["Berenil"], "procedure": "1. 3.5mg/kg deep IM\n2. Single dose usually sufficient"}], "prevention": "Tsetse control, prophylactic drugs", "severity": "Severe", "specialist_required": True, "local_names": ["Matenda a tsetse"], "withdrawal_period": "21 days"}
        ]
    },
    "chickens": {
        "diseases": [
            {"name": "Newcastle Disease", "symptoms": ["sudden death", "twisted necks", "green diarrhea", "drop in eggs"], "causes": ["NDV"], "treatments": [{"type": "vaccine", "name": "NDV Lasota vaccine", "active_ingredients": ["Live attenuated NDV"], "trade_names": ["NDV Lasota"], "procedure": "1. Vaccinate all birds\n2. Eye drop or drinking water\n3. Revaccinate after 3-4 weeks"}], "prevention": "Vaccination, biosecurity, quarantine", "severity": "Critical", "specialist_required": True, "local_names": ["Chilala cha nkhuku"], "withdrawal_period": "N/A"},
            {"name": "Fowl Pox", "symptoms": ["wart-like lesions on comb", "scabs on skin", "difficulty breathing"], "causes": ["Fowl pox virus"], "treatments": [{"type": "supportive", "name": "Supportive care", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. Apply iodine to scabs\n2. Isolate affected birds\n3. Provide soft feed"}], "prevention": "Vaccination, mosquito control", "severity": "Moderate", "specialist_required": False, "local_names": ["Mphutsi wa nkhuku"], "withdrawal_period": "N/A"},
            {"name": "Coccidiosis", "symptoms": ["bloody diarrhea", "ruffled feathers", "lethargy", "pale comb"], "causes": ["Eimeria"], "treatments": [{"type": "chemical", "name": "Amprolium", "active_ingredients": ["Amprolium"], "trade_names": ["Amprol"], "procedure": "1. 30g per 4.5L water for 5-7 days\n2. Then 15g per 4.5L for 7-14 days"}], "prevention": "Coccidiostats in feed, good litter management", "severity": "Severe", "specialist_required": False, "local_names": ["Chilala cha m'mimba"], "withdrawal_period": "3 days"}
        ]
    },
    "goats": {
        "diseases": [
            {"name": "Heartwater", "symptoms": ["fever", "nervous signs", "circling", "convulsions", "sudden death"], "causes": ["Ehrlichia ruminantium"], "treatments": [{"type": "chemical", "name": "Oxytetracycline 20% LA", "active_ingredients": ["Oxytetracycline"], "trade_names": ["Terramycin LA"], "procedure": "1. 20mg/kg IV or IM\n2. Repeat daily for 3-5 days\n3. Early treatment critical"}], "prevention": "Tick control, vaccination, tick-resistant breeds", "severity": "Critical", "specialist_required": True, "local_names": ["Matenda a mtima"], "withdrawal_period": "21 days"},
            {"name": "CCPP", "symptoms": ["severe coughing", "nasal discharge", "fever", "difficulty breathing"], "causes": ["Mycoplasma capricolum"], "treatments": [{"type": "chemical", "name": "Oxytetracycline + Tylosin", "active_ingredients": ["Oxytetracycline", "Tylosin"], "trade_names": ["Terramycin + Tylan"], "procedure": "1. Oxytetracycline 20mg/kg IM\n2. Tylosin 10mg/kg IM daily\n3. Isolate affected animals"}], "prevention": "Vaccination, quarantine new animals, avoid communal grazing", "severity": "Critical", "specialist_required": True, "local_names": ["Chilala cha mphepo"], "withdrawal_period": "21 days"}
        ]
    },
    "pigs": {
        "diseases": [
            {"name": "African Swine Fever", "symptoms": ["high fever", "red skin blotches", "vomiting", "diarrhea", "sudden death"], "causes": ["ASFV"], "treatments": [{"type": "biosecurity", "name": "NO TREATMENT - Report and cull", "active_ingredients": ["N/A"], "trade_names": ["N/A"], "procedure": "1. REPORT IMMEDIATELY to authorities\n2. Quarantine entire farm\n3. Cull all affected pigs\n4. Deep burial or burning\n5. Thorough disinfection"}], "prevention": "Strict biosecurity, no swill feeding, quarantine, fencing", "severity": "Critical", "specialist_required": True, "local_names": ["Chilala cha nkhumba"], "withdrawal_period": "N/A"}
        ]
    }
}

MALAWI_LOCATIONS = {
    "veterinary_clinics": [
        {"name": "Lilongwe Central Veterinary Lab", "type": "Government", "services": ["Diagnosis", "Vaccination", "Lab testing"], "address": "Area 3, Lilongwe", "coordinates": {"lat": -13.9626, "lng": 33.7741}, "contact": "+265-1-754-000", "hours": "Mon-Fri 08:00-16:00", "region": "Central"},
        {"name": "Blantyre Veterinary Office", "type": "Government", "services": ["Clinical", "Vaccination"], "address": "Chichiri, Blantyre", "coordinates": {"lat": -15.8019, "lng": 35.0218}, "contact": "+265-1-822-000", "hours": "Mon-Fri 08:00-16:00", "region": "Southern"},
        {"name": "Mzuzu Veterinary Office", "type": "Government", "services": ["Clinical", "Vaccination"], "address": "Mzuzu City", "coordinates": {"lat": -11.4600, "lng": 34.0200}, "contact": "+265-1-333-000", "hours": "Mon-Fri 08:00-16:00", "region": "Northern"},
        {"name": "Zomba Veterinary Office", "type": "Government", "services": ["Clinical", "Post-mortem"], "address": "Zomba", "coordinates": {"lat": -15.3900, "lng": 35.3200}, "contact": "+265-1-525-000", "hours": "Mon-Fri 08:00-16:00", "region": "Southern"},
        {"name": "Kasungu Veterinary Office", "type": "Government", "services": ["Clinical", "Extension"], "address": "Kasungu Boma", "coordinates": {"lat": -13.0333, "lng": 33.4833}, "contact": "+265-1-762-000", "hours": "Mon-Fri 08:00-16:00", "region": "Central"},
        {"name": "Agricare Veterinary Services", "type": "Private", "services": ["Clinical", "Surgery", "Pharmacy"], "address": "Area 47, Lilongwe", "coordinates": {"lat": -13.9500, "lng": 33.7800}, "contact": "+265-888-123-456", "hours": "Mon-Sat 08:00-18:00", "region": "Central"},
        {"name": "Shire Veterinary Clinic", "type": "Private", "services": ["Clinical", "Pharmacy", "Lab"], "address": "Ndirande, Blantyre", "coordinates": {"lat": -15.7900, "lng": 35.0300}, "contact": "+265-999-456-789", "hours": "Mon-Sat 08:00-17:00", "region": "Southern"}
    ],
    "agro_dealers": [
        {"name": "Farmers World Limited", "type": "Agro-dealer", "products": ["Fertilizers", "Seeds", "Pesticides", "Vet drugs"], "address": "Kanengo, Lilongwe", "coordinates": {"lat": -13.9000, "lng": 33.8000}, "contact": "+265-1-711-000", "hours": "Mon-Fri 08:00-17:00", "region": "Central"},
        {"name": "Agro-Chem Ltd", "type": "Agro-dealer", "products": ["Pesticides", "Fungicides", "Herbicides", "Vet supplies"], "address": "Limbe, Blantyre", "coordinates": {"lat": -15.8100, "lng": 35.0200}, "contact": "+265-1-844-000", "hours": "Mon-Fri 08:00-17:00", "region": "Southern"},
        {"name": "Peoples Trading Centre (PTC)", "type": "General Store", "products": ["Basic agrochemicals", "Seeds", "Fertilizers"], "address": "Multiple locations", "coordinates": {"lat": -13.9626, "lng": 33.7741}, "contact": "Various", "hours": "Mon-Sat 08:00-17:00", "region": "National"},
        {"name": "Malawi Fertilizer Company", "type": "Manufacturer", "products": ["Fertilizers", "Agrochemicals"], "address": "Kanengo, Lilongwe", "coordinates": {"lat": -13.9100, "lng": 33.8050}, "contact": "+265-1-711-111", "hours": "Mon-Fri 08:00-17:00", "region": "Central"},
        {"name": "Export Trading Group (ETG)", "type": "Agro-dealer", "products": ["Seeds", "Fertilizers", "Pesticides", "Grain storage"], "address": "Lilongwe and Blantyre", "coordinates": {"lat": -13.9700, "lng": 33.7700}, "contact": "+265-1-794-000", "hours": "Mon-Fri 08:00-17:00", "region": "Central/Southern"}
    ],
    "extension_offices": [
        {"name": "DAES - Lilongwe ADD", "type": "Extension", "services": ["Technical advice", "Training", "Demo plots"], "address": "Lilongwe", "coordinates": {"lat": -13.9626, "lng": 33.7741}, "contact": "+265-1-789-200", "hours": "Mon-Fri 08:00-16:00", "region": "Central"},
        {"name": "DAES - Blantyre ADD", "type": "Extension", "services": ["Technical advice", "Training", "Demo plots"], "address": "Blantyre", "coordinates": {"lat": -15.8019, "lng": 35.0218}, "contact": "+265-1-822-000", "hours": "Mon-Fri 08:00-16:00", "region": "Southern"},
        {"name": "DAES - Mzuzu ADD", "type": "Extension", "services": ["Technical advice", "Training", "Demo plots"], "address": "Mzuzu", "coordinates": {"lat": -11.4600, "lng": 34.0200}, "contact": "+265-1-333-000", "hours": "Mon-Fri 08:00-16:00", "region": "Northern"}
    ]
}

PLANT_CATEGORIES = ["Maize", "Groundnuts", "Soybeans", "Tobacco", "Cassava", "Sweet Potatoes", "Rice", "Sorghum", "Beans", "Cowpeas", "Cotton", "Tea", "Coffee", "Tomatoes"]
LIVESTOCK_CATEGORIES = ["Cattle", "Goats", "Sheep", "Pigs", "Chickens", "Ducks", "Rabbits", "Donkeys"]
EMERGENCY_CONTACTS = {"Department of Animal Health": "+265-1-789-400", "Ministry of Agriculture": "+265-1-789-200", "Lilongwe Veterinary Office": "+265-1-754-000", "Blantyre Veterinary Office": "+265-1-822-000"}

# ============================================================
# GEMINI AI ENGINE - Using REST API directly (more reliable)
# ============================================================
class GeminiEngine:
    def __init__(self):
        self.api_key = "AQ.Ab8RN6I42spk2PwgFLAwrj69tv0cixLRKM6rP67j0_pn4R_AHQ"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.available = self._test_connection()

    def _test_connection(self):
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": "Hello"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            url = self.api_url + "?key=" + self.api_key
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False

    def analyze_plant_image(self, image, crop_type=None):
        if not self.available:
            return self._default("AI service not available. Using local database.")
        try:
            # Convert image to bytes for API
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            import base64
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

            prompt_text = "You are an agricultural expert in Malawi. Analyze this plant image and identify the disease, confidence, symptoms, immediate actions, and severity. Respond ONLY in JSON format with these exact fields: disease_name, confidence (High/Medium/Low), symptoms (array), immediate_actions (array), specialist_needed (true/false), severity (Mild/Moderate/Severe/Critical), notes."
            if crop_type:
                prompt_text += " Crop type: " + crop_type

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {"inline_data": {"mime_type": "image/png", "data": img_base64}}
                    ]
                }],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 1000}
            }

            url = self.api_url + "?key=" + self.api_key
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                # Extract JSON from text
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            return self._default("Could not parse AI response")
        except Exception as e:
            return self._default(str(e))

    def analyze_livestock_symptoms(self, symptoms, animal_type):
        if not self.available:
            return self._default_livestock("AI service not available. Using local database.")
        try:
            prompt_text = "You are a veterinary expert in Malawi. Animal: " + animal_type + ". Symptoms: " + symptoms + ". Provide diagnosis ONLY in JSON format with these exact fields: primary_diagnosis, confidence (High/Medium/Low), differential_diagnoses (array), first_aid (array), emergency (true/false), risk_level (Low/Medium/High/Critical), recommendations."

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 1000}
            }

            url = self.api_url + "?key=" + self.api_key
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            return self._default_livestock("Could not parse AI response")
        except Exception as e:
            return self._default_livestock(str(e))

    def get_treatment_recommendations(self, diagnosis, category):
        if not self.available:
            return {}
        try:
            prompt_text = "You are an agricultural extension expert in Malawi. Disease: " + diagnosis["disease_name"] + ". Provide treatment recommendations in JSON with: chemical_treatments (array of objects with name, active_ingredient, trade_names, dosage, application, frequency), organic_treatments (array), cultural_practices (array), prevention (array), recovery_timeline, warnings (array)."

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 1500}
            }

            url = self.api_url + "?key=" + self.api_key
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            return {}
        except:
            return {}

    def _default(self, error=None):
        return {"disease_name": "Unable to identify", "confidence": "Low", "symptoms": [], "immediate_actions": ["Consult local agricultural extension officer"], "specialist_needed": True, "severity": "Unknown", "notes": error or "Analysis failed"}

    def _default_livestock(self, error=None):
        return {"primary_diagnosis": "Unable to determine", "confidence": "Low", "differential_diagnoses": [], "first_aid": ["Contact veterinarian immediately"], "emergency": True, "risk_level": "Unknown", "recommendations": error or "Analysis failed"}

gemini_engine = GeminiEngine()

# ============================================================
# IMAGE PROCESSOR
# ============================================================
class ImageProcessor:
    def enhance_image(self, image):
        img_array = np.array(image)
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    def detect_disease_regions(self, image):
        img_array = np.array(image)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([40, 255, 255])
        lower_brown = np.array([10, 100, 20])
        upper_brown = np.array([30, 255, 200])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        disease_mask = cv2.bitwise_or(mask_yellow, mask_brown)
        contours, _ = cv2.findContours(disease_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = img_array.copy()
        cv2.drawContours(result, contours, -1, (255, 0, 0), 2)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        affected_pixels = cv2.countNonZero(disease_mask)
        affected_percentage = (affected_pixels / total_pixels) * 100
        return result, affected_percentage, contours

    def extract_features(self, image):
        img_array = np.array(image)
        mean_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array, axis=(0, 1))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        texture = cv2.Laplacian(gray, cv2.CV_64F).var()
        _, _, contours = self.detect_disease_regions(image)
        if contours:
            areas = [cv2.contourArea(c) for c in contours]
            return {"mean_rgb": mean_color.tolist(), "std_rgb": std_color.tolist(), "texture": texture, "lesion_count": len(contours), "max_lesion_area": max(areas), "avg_lesion_area": np.mean(areas)}
        return {"mean_rgb": mean_color.tolist(), "std_rgb": std_color.tolist(), "texture": texture, "lesion_count": 0, "max_lesion_area": 0, "avg_lesion_area": 0}

image_processor = ImageProcessor()

# ============================================================
# GEOLOCATION
# ============================================================
class GeolocationService:
    def __init__(self):
        self.locations_data = MALAWI_LOCATIONS

    def get_user_location(self):
        return {"lat": -13.9626, "lng": 33.7741, "name": "Lilongwe, Malawi"}

    def find_nearby(self, user_location, location_type="all", radius_km=50):
        nearby = []
        categories = ["veterinary_clinics", "agro_dealers", "extension_offices"] if location_type == "all" else [location_type]
        for category in categories:
            for place in self.locations_data.get(category, []):
                distance = geodesic((user_location["lat"], user_location["lng"]), (place["coordinates"]["lat"], place["coordinates"]["lng"])).kilometers
                if distance <= radius_km:
                    place_copy = place.copy()
                    place_copy["distance_km"] = round(distance, 2)
                    place_copy["category"] = category
                    nearby.append(place_copy)
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby

    def get_directions_link(self, origin, destination):
        return "https://www.google.com/maps/dir/?api=1&origin=" + str(origin["lat"]) + "," + str(origin["lng"]) + "&destination=" + str(destination["lat"]) + "," + str(destination["lng"]) + "&travelmode=driving"

    def create_map(self, user_location, places=None, zoom=10):
        m = folium.Map(location=[user_location["lat"], user_location["lng"]], zoom_start=zoom, tiles="OpenStreetMap")
        folium.Marker([user_location["lat"], user_location["lng"]], popup="Your Location", icon=folium.Icon(color="blue", icon="user", prefix="fa"), tooltip="You are here").add_to(m)
        if places:
            colors = {"veterinary_clinics": "red", "agro_dealers": "green", "extension_offices": "orange"}
            icons = {"veterinary_clinics": "medkit", "agro_dealers": "shopping-cart", "extension_offices": "info-circle"}
            for place in places:
                popup_html = "<b>" + place["name"] + "</b><br>Type: " + place["type"] + "<br>Distance: " + str(place.get("distance_km", "N/A")) + " km<br>Contact: " + place.get("contact", "N/A") + "<br>Hours: " + place.get("hours", "N/A") + "<br><a href=\"" + self.get_directions_link(user_location, place["coordinates"]) + "\" target=\"_blank\">Get Directions</a>"
                folium.Marker([place["coordinates"]["lat"], place["coordinates"]["lng"]], popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=colors.get(place["category"], "gray"), icon=icons.get(place["category"], "info"), prefix="fa"), tooltip=place["name"]).add_to(m)
        return m

geolocation_service = GeolocationService()

# ============================================================
# DATABASE
# ============================================================
class Database:
    def __init__(self):
        self.history_file = "diagnosis_history.json"
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def load_disease_data(self, category):
        if category == "plant":
            return PLANT_DISEASES
        elif category == "livestock":
            return LIVESTOCK_DISEASES
        elif category == "locations":
            return MALAWI_LOCATIONS
        return {}

    def save_diagnosis(self, diagnosis_data):
        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)
        except:
            history = []
        diagnosis_data["timestamp"] = datetime.now().isoformat()
        diagnosis_data["id"] = len(history) + 1
        history.append(diagnosis_data)
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)
        return diagnosis_data["id"]

    def get_history(self, limit=50):
        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)
            return history[-limit:][::-1]
        except:
            return []

    def get_statistics(self):
        history = self.get_history(limit=1000)
        stats = {"total_diagnoses": len(history), "plant_vs_livestock": {"plant": 0, "livestock": 0}, "severity_distribution": {}, "common_diseases": {}}
        for entry in history:
            category = entry.get("category", "unknown")
            stats["plant_vs_livestock"][category] = stats["plant_vs_livestock"].get(category, 0) + 1
            severity = entry.get("severity", "unknown")
            stats["severity_distribution"][severity] = stats["severity_distribution"].get(severity, 0) + 1
            disease = entry.get("disease_name", "unknown")
            stats["common_diseases"][disease] = stats["common_diseases"].get(disease, 0) + 1
        stats["common_diseases"] = dict(sorted(stats["common_diseases"].items(), key=lambda x: x[1], reverse=True)[:10])
        return stats

db = Database()

# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(page_title="AgriSmart Malawi", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main-header { font-size: 3rem; font-weight: bold; color: #2E7D32; text-align: center; }
.sub-header { font-size: 1.2rem; color: #555; text-align: center; }
.card { background-color: #f0f2f6; border-radius: 10px; padding: 20px; margin: 10px 0; border-left: 5px solid #2E7D32; }
.emergency { background-color: #ffebee; border-left: 5px solid #c62828; padding: 15px; border-radius: 5px; }
.treatment-step { background-color: #e8f5e9; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #4caf50; }
.stButton>button { background-color: #2E7D32; color: white; border-radius: 20px; padding: 10px 24px; font-weight: bold; }
.severity-mild { color: #4caf50; font-weight: bold; }
.severity-moderate { color: #ff9800; font-weight: bold; }
.severity-severe { color: #f44336; font-weight: bold; }
.severity-critical { color: #b71c1c; font-weight: bold; }
.ai-status { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
.ai-online { background-color: #e8f5e9; color: #2e7d32; }
.ai-offline { background-color: #fff3e0; color: #e65100; }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if "current_diagnosis" not in st.session_state:
        st.session_state.current_diagnosis = None
    if "user_location" not in st.session_state:
        st.session_state.user_location = geolocation_service.get_user_location()

def render_header():
    st.markdown('<div class="main-header">🌾 AgriSmart Malawi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Agricultural Diagnosis & Treatment Advisor</div>', unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.title("🌾 AgriSmart")
        st.markdown("---")
        page = st.radio("Select Service", ["🏠 Home", "🌱 Plant Diagnosis", "🐄 Livestock Diagnosis", "📍 Find Services", "📚 Disease Library", "📊 History & Stats"])
        st.divider()
        st.subheader("🌐 Language")
        st.selectbox("Select Language", ["English", "Chichewa (coming soon)"])
        st.divider()
        st.subheader("🚨 Emergency Contacts")
        for name, number in EMERGENCY_CONTACTS.items():
            st.markdown("**" + name + "**  \n📞 " + number)
        st.divider()
        st.caption("2024 AgriSmart Malawi v1.0")
        return page

def render_home():
    # AI Status indicator
    if gemini_engine.available:
        st.markdown('<div class="ai-status ai-online">✅ AI Engine Online - Gemini is ready to analyze your crops and animals</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ai-status ai-offline">⚠️ AI Engine Offline - Using local database only. Check your internet connection.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card"><h3>🌱 Plant Health</h3><p>Diagnose crop diseases using photos or symptom descriptions.</p></div>', unsafe_allow_html=True)
        if st.button("Diagnose Plant", key="btn_plant", use_container_width=True):
            st.session_state.page = "🌱 Plant Diagnosis"
            st.rerun()
    with col2:
        st.markdown('<div class="card"><h3>🐄 Livestock Health</h3><p>Analyze animal symptoms and get veterinary advice.</p></div>', unsafe_allow_html=True)
        if st.button("Diagnose Animal", key="btn_livestock", use_container_width=True):
            st.session_state.page = "🐄 Livestock Diagnosis"
            st.rerun()
    with col3:
        st.markdown('<div class="card"><h3>📍 Local Services</h3><p>Find veterinary clinics, agro-dealers, and extension offices.</p></div>', unsafe_allow_html=True)
        if st.button("Find Services", key="btn_services", use_container_width=True):
            st.session_state.page = "📍 Find Services"
            st.rerun()
    st.divider()
    st.subheader("📊 Quick Stats")
    stats = db.get_statistics()
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Diagnoses", stats["total_diagnoses"])
    with cols[1]:
        st.metric("Plant Cases", stats["plant_vs_livestock"].get("plant", 0))
    with cols[2]:
        st.metric("Livestock Cases", stats["plant_vs_livestock"].get("livestock", 0))
    with cols[3]:
        critical = sum(1 for s, c in stats["severity_distribution"].items() if s in ["Severe", "Critical"])
        st.metric("Critical Cases", critical)

def render_plant_diagnosis():
    st.header("🌱 Plant Disease Diagnosis")

    # Show AI status
    if gemini_engine.available:
        st.success("✅ AI is online and ready to analyze your plant images!")
    else:
        st.warning("⚠️ AI is offline. The app will use the local disease database for recommendations.")

    input_method = st.radio("Select Input Method", ["📷 Take Photo", "🖼️ Upload Image", "✍️ Describe Symptoms"], horizontal=True)
    crop_type = st.selectbox("Select Crop Type", PLANT_CATEGORIES, index=0)
    image = None
    symptoms_text = ""
    if input_method == "📷 Take Photo":
        camera_image = st.camera_input("Take a photo of the affected plant")
        if camera_image:
            image = Image.open(camera_image)
    elif input_method == "🖼️ Upload Image":
        uploaded_file = st.file_uploader("Upload plant image", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file:
            image = Image.open(uploaded_file)
    else:
        symptoms_text = st.text_area("Describe the symptoms you observe", placeholder="Example: Yellow spots on maize leaves...", height=150)
    if image:
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original Image", use_container_width=True)
        with col2:
            enhanced = image_processor.enhance_image(image)
            st.image(enhanced, caption="Enhanced for Analysis", use_container_width=True)
    if st.button("🔍 Analyze with AI", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing your plant... Please wait"):
            if image:
                features = image_processor.extract_features(image)
                ai_result = gemini_engine.analyze_plant_image(image, crop_type)
                analyzed_img, affected_pct, contours = image_processor.detect_disease_regions(image)
                local_data = db.load_disease_data("plant")
                crop_data = local_data.get(crop_type.lower(), {})
                diagnosis = {
                    "category": "plant", "crop_type": crop_type,
                    "disease_name": ai_result.get("disease_name", "Unknown"),
                    "confidence": ai_result.get("confidence", "Low"),
                    "symptoms": ai_result.get("symptoms", []),
                    "severity": ai_result.get("severity", "Moderate"),
                    "specialist_needed": ai_result.get("specialist_needed", False),
                    "affected_area_pct": round(affected_pct, 2),
                    "features": features, "ai_analysis": ai_result,
                    "local_matches": crop_data
                }
                treatment = gemini_engine.get_treatment_recommendations(diagnosis, "plant")
                diagnosis["treatment"] = treatment
            else:
                ai_result = gemini_engine.analyze_livestock_symptoms(symptoms_text, crop_type)
                diagnosis = {
                    "category": "plant", "crop_type": crop_type,
                    "disease_name": ai_result.get("primary_diagnosis", "Unknown"),
                    "confidence": ai_result.get("confidence", "Low"),
                    "symptoms": symptoms_text.split("\n"),
                    "severity": ai_result.get("risk_level", "Moderate"),
                    "specialist_needed": ai_result.get("emergency", False),
                    "ai_analysis": ai_result
                }
            db.save_diagnosis(diagnosis)
            st.session_state.current_diagnosis = diagnosis
            st.success("Analysis Complete!")
            st.rerun()
    if st.session_state.current_diagnosis and st.session_state.current_diagnosis.get("category") == "plant":
        display_diagnosis_result(st.session_state.current_diagnosis)

def render_livestock_diagnosis():
    st.header("🐄 Livestock Health Diagnosis")

    # Show AI status
    if gemini_engine.available:
        st.success("✅ AI is online and ready to analyze your animal symptoms!")
    else:
        st.warning("⚠️ AI is offline. The app will use the local disease database for recommendations.")

    animal_type = st.selectbox("Select Animal Type", LIVESTOCK_CATEGORIES, index=0)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Symptom Checklist")
        symptoms = {
            "General": ["Fever", "Loss of appetite", "Weight loss", "Weakness", "Lethargy"],
            "Digestive": ["Diarrhea", "Constipation", "Bloating", "Vomiting", "Blood in feces"],
            "Respiratory": ["Coughing", "Nasal discharge", "Difficulty breathing", "Rapid breathing"],
            "Skin/External": ["Skin lesions", "Hair loss", "Swelling", "Lameness", "Ticks visible"],
            "Neurological": ["Trembling", "Circling", "Blindness", "Paralysis", "Convulsions"]
        }
        selected_symptoms = []
        for category, symptom_list in symptoms.items():
            st.markdown("**" + category + "**")
            for symptom in symptom_list:
                if st.checkbox(symptom, key="sym_" + symptom):
                    selected_symptoms.append(symptom)
    with col2:
        st.subheader("Additional Details")
        photo = st.file_uploader("Upload photo (optional)", type=["jpg", "jpeg", "png", "webp"])
        if photo:
            st.image(photo, caption="Animal Photo", use_container_width=True)
        notes = st.text_area("Additional observations", placeholder="When did symptoms start?", height=150)
        severity = st.slider("How severe?", 1, 10, 5)
        num_affected = st.number_input("Number affected", min_value=1, value=1)
    all_symptoms = selected_symptoms + ([notes] if notes else [])
    symptoms_text = ", ".join(all_symptoms) if all_symptoms else "No specific symptoms selected"
    if st.button("🔍 Analyze with AI", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing your animal symptoms... Please wait"):
            ai_result = gemini_engine.analyze_livestock_symptoms(symptoms_text, animal_type)
            local_data = db.load_disease_data("livestock")
            animal_data = local_data.get(animal_type.lower(), {})
            diagnosis = {
                "category": "livestock", "animal_type": animal_type,
                "disease_name": ai_result.get("primary_diagnosis", "Unknown"),
                "confidence": ai_result.get("confidence", "Low"),
                "symptoms": all_symptoms,
                "severity": ai_result.get("risk_level", "Moderate"),
                "specialist_needed": ai_result.get("emergency", False),
                "num_affected": num_affected,
                "severity_score": severity,
                "ai_analysis": ai_result,
                "local_matches": animal_data
            }
            db.save_diagnosis(diagnosis)
            st.session_state.current_diagnosis = diagnosis
            st.success("Analysis Complete!")
            st.rerun()
    if st.session_state.current_diagnosis and st.session_state.current_diagnosis.get("category") == "livestock":
        display_diagnosis_result(st.session_state.current_diagnosis)

def display_diagnosis_result(diagnosis):
    st.divider()
    severity_class = "severity-" + diagnosis["severity"].lower()
    st.markdown('<div style="text-align: center; padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin: 20px 0;"><h2>Diagnosis: ' + diagnosis["disease_name"] + '</h2><p>Confidence: <strong>' + diagnosis["confidence"] + '</strong> | Severity: <span class="' + severity_class + '">' + diagnosis["severity"] + '</span></p></div>', unsafe_allow_html=True)
    if diagnosis.get("specialist_needed") or diagnosis["severity"] in ["Severe", "Critical"]:
        st.markdown('<div class="emergency"><h3>🚨 URGENT: Specialist Intervention Required</h3><p>This condition requires immediate professional attention.</p></div>', unsafe_allow_html=True)
        st.subheader("📍 Nearby Veterinary Services")
        user_loc = st.session_state.user_location
        nearby_vets = geolocation_service.find_nearby(user_loc, "veterinary_clinics", 100)
        if nearby_vets:
            for vet in nearby_vets[:3]:
                with st.container():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown("**" + vet["name"] + "**  \n📍 " + str(vet["distance_km"]) + " km | " + vet["address"] + "  \n📞 " + vet["contact"] + " | 🕐 " + vet["hours"])
                    with cols[1]:
                        st.link_button("Get Directions", geolocation_service.get_directions_link(user_loc, vet["coordinates"]), use_container_width=True)
        else:
            st.info("No veterinary clinics found within 100km.")
    with st.expander("🔍 Identified Symptoms", expanded=True):
        if isinstance(diagnosis["symptoms"], list):
            for symptom in diagnosis["symptoms"]:
                st.markdown("- " + symptom)
        else:
            st.markdown(diagnosis["symptoms"])
    st.subheader("💊 Treatment Recommendations")
    category = diagnosis["category"]
    local_data = db.load_disease_data(category)
    if category == "plant":
        crop = diagnosis.get("crop_type", "").lower()
        disease_name = diagnosis["disease_name"]
        crop_diseases = local_data.get(crop, {}).get("diseases", [])
        matched_disease = next((d for d in crop_diseases if disease_name.lower() in d["name"].lower()), None)
    else:
        animal = diagnosis.get("animal_type", "").lower()
        disease_name = diagnosis["disease_name"]
        animal_diseases = local_data.get(animal, {}).get("diseases", [])
        matched_disease = next((d for d in animal_diseases if disease_name.lower() in d["name"].lower()), None)
    if matched_disease:
        for i, treatment in enumerate(matched_disease.get("treatments", [])):
            with st.container():
                st.markdown('<div class="treatment-step"><h4>' + str(i+1) + ". " + treatment["name"] + '</h4><p><strong>Type:</strong> ' + treatment["type"].title() + '</p><p><strong>Active Ingredients:</strong> ' + ", ".join(treatment["active_ingredients"]) + '</p><p><strong>Available as:</strong> ' + ", ".join(treatment["trade_names"]) + '</p><p><strong>Procedure:</strong></p></div>', unsafe_allow_html=True)
                st.markdown(treatment["procedure"])
                if treatment.get("withdrawal_period"):
                    st.info("⏱️ Withdrawal Period: " + treatment["withdrawal_period"])
        st.subheader("🛡️ Prevention Measures")
        st.markdown(matched_disease.get("prevention", "No specific prevention data available."))
        if matched_disease.get("local_names"):
            st.caption("🗣️ Local name(s): " + ", ".join(matched_disease["local_names"]))
    else:
        treatment = diagnosis.get("treatment", {})
        if treatment.get("chemical_treatments"):
            st.markdown("**Chemical Treatments:**")
            for chem in treatment["chemical_treatments"]:
                with st.container():
                    st.markdown('<div class="treatment-step"><h4>' + chem["name"] + '</h4><p>Active Ingredient: ' + chem.get("active_ingredient", "N/A") + '</p><p>Dosage: ' + chem.get("dosage", "N/A") + '</p></div>', unsafe_allow_html=True)
        if treatment.get("organic_treatments"):
            st.markdown("**Organic/Traditional Treatments:**")
            for org in treatment["organic_treatments"]:
                st.markdown("- **" + org["name"] + "**: " + org.get("preparation", ""))
    st.subheader("🛒 Find Medication & Supplies")
    user_loc = st.session_state.user_location
    nearby_dealers = geolocation_service.find_nearby(user_loc, "agro_dealers", 100)
    if nearby_dealers:
        for dealer in nearby_dealers[:3]:
            with st.container():
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown("**" + dealer["name"] + "** (" + dealer["type"] + ")  \n📍 " + str(dealer["distance_km"]) + " km | " + dealer["address"] + "  \n📞 " + dealer["contact"] + " | 🕐 " + dealer["hours"] + "  \n🏷️ Products: " + ", ".join(dealer["products"][:3]))
                with cols[1]:
                    st.link_button("Directions", geolocation_service.get_directions_link(user_loc, dealer["coordinates"]), use_container_width=True)
    else:
        st.info("No agro-dealers found nearby.")
    st.subheader("🗺️ Service Locations Map")
    all_places = geolocation_service.find_nearby(user_loc, "all", 100)
    m = geolocation_service.create_map(user_loc, all_places[:10])
    try:
        from streamlit_folium import st_folium
        st_folium(m, width=700, height=400)
    except:
        st.info("Map feature requires streamlit-folium.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 New Diagnosis", use_container_width=True):
            st.session_state.current_diagnosis = None
            st.rerun()
    with col2:
        if st.button("📞 Call Vet Emergency", use_container_width=True):
            st.markdown("📞 **+265-1-789-400** (Department of Animal Health)")
    with col3:
        if st.button("📋 Save Report", use_container_width=True):
            st.success("Report saved to history!")

def render_find_services():
    st.header("📍 Find Agricultural Services")
    col1, col2 = st.columns([2, 1])
    with col1:
        region = st.selectbox("Select Region", ["All", "Central", "Southern", "Northern"])
    with col2:
        service_type = st.selectbox("Service Type", ["All", "veterinary_clinics", "agro_dealers", "extension_offices"])
    radius = st.slider("Search Radius (km)", 5, 200, 50)
    user_loc = st.session_state.user_location
    if st.button("🔍 Search", type="primary"):
        places = geolocation_service.find_nearby(user_loc, service_type, radius)
        if region != "All":
            places = [p for p in places if p.get("region") == region]
        st.subheader("Found " + str(len(places)) + " services within " + str(radius) + "km")
        m = geolocation_service.create_map(user_loc, places, zoom=8)
        try:
            from streamlit_folium import st_folium
            st_folium(m, width=700, height=500)
        except:
            st.info("Map feature requires streamlit-folium.")
        for place in places:
            with st.container():
                st.markdown('<div class="card"><h4>' + place["name"] + '</h4><p><strong>Type:</strong> ' + place["type"] + ' | <strong>Distance:</strong> ' + str(place["distance_km"]) + ' km</p><p>📍 ' + place["address"] + '</p><p>📞 ' + place.get("contact", "N/A") + ' | 🕐 ' + place.get("hours", "N/A") + '</p></div>', unsafe_allow_html=True)
                st.link_button("Get Directions", geolocation_service.get_directions_link(user_loc, place["coordinates"]), use_container_width=True)

def render_disease_library():
    st.header("📚 Disease Library")
    tab1, tab2 = st.tabs(["🌱 Plant Diseases", "🐄 Livestock Diseases"])
    with tab1:
        crop = st.selectbox("Select Crop", PLANT_CATEGORIES)
        plant_data = db.load_disease_data("plant")
        crop_info = plant_data.get(crop.lower(), {})
        if crop_info:
            for disease in crop_info.get("diseases", []):
                with st.expander("🔴 " + disease["name"] + " (Severity: " + disease["severity"] + ")"):
                    st.markdown("**Symptoms:** " + ", ".join(disease["symptoms"]))
                    st.markdown("**Causes:** " + ", ".join(disease["causes"]))
                    st.markdown("**Prevention:** " + disease["prevention"])
                    if disease.get("local_names"):
                        st.caption("Local names: " + ", ".join(disease["local_names"]))
                    if disease.get("specialist_required"):
                        st.warning("⚠️ Requires specialist intervention")
        else:
            st.info("No data available for this crop yet.")
    with tab2:
        animal = st.selectbox("Select Animal", LIVESTOCK_CATEGORIES)
        livestock_data = db.load_disease_data("livestock")
        animal_info = livestock_data.get(animal.lower(), {})
        if animal_info:
            for disease in animal_info.get("diseases", []):
                with st.expander("🔴 " + disease["name"] + " (Severity: " + disease["severity"] + ")"):
                    st.markdown("**Symptoms:** " + ", ".join(disease["symptoms"]))
                    st.markdown("**Causes:** " + ", ".join(disease["causes"]))
                    st.markdown("**Prevention:** " + disease["prevention"])
                    if disease.get("withdrawal_period"):
                        st.info("⏱️ Withdrawal period: " + disease["withdrawal_period"])
                    if disease.get("specialist_required"):
                        st.warning("⚠️ Requires specialist intervention")
        else:
            st.info("No data available for this animal yet.")

def render_history():
    st.header("📊 Diagnosis History & Statistics")
    tab1, tab2 = st.tabs(["📜 History", "📈 Statistics"])
    with tab1:
        history = db.get_history(limit=50)
        if history:
            for entry in history:
                with st.container():
                    emoji = "🌱" if entry["category"] == "plant" else "🐄"
                    st.markdown('<div class="card"><h4>' + emoji + " " + entry["disease_name"] + '</h4><p>Date: ' + entry["timestamp"][:10] + ' | Category: ' + entry["category"].title() + ' | Severity: ' + entry.get("severity", "Unknown") + '</p></div>', unsafe_allow_html=True)
        else:
            st.info("No diagnosis history yet.")
    with tab2:
        stats = db.get_statistics()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Diagnoses", stats["total_diagnoses"])
        with col2:
            st.metric("Plant Cases", stats["plant_vs_livestock"].get("plant", 0))
        with col3:
            st.metric("Livestock Cases", stats["plant_vs_livestock"].get("livestock", 0))
        if stats["severity_distribution"]:
            st.subheader("Severity Distribution")
            severity_df = pd.DataFrame([{"Severity": k, "Count": v} for k, v in stats["severity_distribution"].items()])
            st.bar_chart(severity_df.set_index("Severity"))
        if stats["common_diseases"]:
            st.subheader("Most Common Diagnoses")
            common_df = pd.DataFrame([{"Disease": k, "Count": v} for k, v in list(stats["common_diseases"].items())[:10]])
            st.bar_chart(common_df.set_index("Disease"))

def main():
    init_session_state()
    render_header()
    page = render_sidebar()
    if page == "🏠 Home":
        render_home()
    elif page == "🌱 Plant Diagnosis":
        render_plant_diagnosis()
    elif page == "🐄 Livestock Diagnosis":
        render_livestock_diagnosis()
    elif page == "📍 Find Services":
        render_find_services()
    elif page == "📚 Disease Library":
        render_disease_library()
    elif page == "📊 History & Stats":
        render_history()

if __name__ == "__main__":
    main()
