import boto3
from PIL import Image, ImageDraw, ImageFont
import io

def analyze_image(bucket, photo):
    client = boto3.client('rekognition')
    
    response = client.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
        MaxLabels=10,
        MinConfidence=70
    )
    return response['Labels']

def download_image_from_s3(bucket, photo):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=photo)
    img_data = obj['Body'].read()
    image = Image.open(io.BytesIO(img_data))
    return image

def draw_bounding_boxes(image, labels):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", size=95)
    label_positions = []

    for label in labels:
        if 'Instances' in label:
            for instance in label['Instances']:
                if instance['Confidence'] > 90:
                    # bouding box coordinates
                    left = image.width * instance['BoundingBox']['Left']
                    top = image.height * instance['BoundingBox']['Top']
                    right = left + image.width * instance['BoundingBox']['Width']
                    bottom = top + image.height * instance['BoundingBox']['Height']

                    draw.rectangle([left, top, right, bottom], outline='red', width=4)

                    text = f"{label['Name']} ({instance['Confidence']:.2f}%)"

                    # use textbbox to get text dimensions
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    # text position
                    text_left = left
                    text_top = top - text_height - 2  

                    # overlap check
                    while any(intersects(text_left, text_top, text_width, text_height, pos) for pos in label_positions):
                        text_top -= (text_height + 2)  # Move up to avoid overlap

                    label_positions.append((text_left, text_top, text_width, text_height))

                    # background
                    draw.rectangle([text_left, text_top, text_left + text_width, text_top + text_height], fill=(255, 255, 255, 180)) 
                    draw.text((text_left, text_top), text, fill='black', font=font)

    return image

def intersects(x1, y1, w1, h1, pos):
    x2, y2, w2, h2 = pos
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)


# usage
bucket = 'your-bucket-name'
photo = 'your-image-file.jpg'

labels = analyze_image(bucket, photo)
image = download_image_from_s3(bucket, photo)  # Download the image from S3
annotated_image = draw_bounding_boxes(image, labels)
annotated_image.save('annotated_image.jpg')

# labels
for label in labels:
    print(f"Label: {label['Name']}, Confidence: {label['Confidence']:.2f}%")
