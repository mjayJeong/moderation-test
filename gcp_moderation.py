from google.cloud import vision

def detect_safe_search(path):
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.safe_search_detection(image=image)
    safe = response.safe_search_annotation

    likelihood_name = (
        "UNKNOWN",
        "VERY_UNLIKELY",
        "UNLIKELY",
        "POSSIBLE",
        "LIKELY",
        "VERY_LIKELY",
    )

    print("Safe search:")
    print(f"adult : {likelihood_name[safe.adult]}")
    print(f"racy : {likelihood_name[safe.racy]}")
    print(f"spoof : {likelihood_name[safe.spoof]}")
    print(f"medical : {likelihood_name[safe.medical]}")
    print(f"violence : {likelihood_name[safe.violence]}")

# 경로 지정
detect_safe_search(" ")
