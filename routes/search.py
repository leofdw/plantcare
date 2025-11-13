from flask import Blueprint, request, jsonify
import requests

search_bp = Blueprint("search", __name__)

API_KEY = "2b10hVFOr8jyBynAO59RdZH"
PROJECT = "all"
BASE_URL = f"https://my-api.plantnet.org/v2/identify/{PROJECT}"

@search_bp.route("/api/search", methods=["POST"])
def identify_plant():
    files = request.files.getlist("images")

    valid_files = []
    for file in files:
        filename = file.filename
        file_content = file.read()
        mime_type = file.content_type or "image/jpeg"
        valid_files.append(("images", (filename, file_content, mime_type)))

    params = {
        "api-key": API_KEY,
        "lang": "ru",
        "nb-results": 3
    }

    data = {
        "organs": ["auto"] * len(valid_files)
    }

    try:
        req = requests.Request(
            "POST",
            url=BASE_URL,
            params=params,
            files=valid_files,
            data=data
        )
        prepared = req.prepare()

        s = requests.Session()
        response = s.send(prepared)
        response.raise_for_status()
        result = response.json()

        plants = []
        for item in result.get("results", [])[:3]:
            s = item["species"]
            common_names = s.get("commonNames", [])
            if isinstance(common_names, list) and len(common_names) > 0:
                name = common_names[0]
            else:
                name = s["scientificNameWithoutAuthor"]
            plants.append({
                "name": name,
                "latin": s["scientificNameWithoutAuthor"],
                "probability": f"{item['score']:.1%}"
            })

        return jsonify({"plants": plants}), 200

    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500
