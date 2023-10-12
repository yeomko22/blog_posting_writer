from PIL import Image


def resize_image(image: Image.Image, max_size: int = 800) -> Image.Image:
    # Get the original image's width and height
    orig_width, orig_height = image.size

    # Check if width is greater than height
    if orig_width >= orig_height:
        # If width is greater, set new width to max_size and scale height proportionally
        ratio = max_size / float(orig_width)
        new_height = int(float(orig_height) * float(ratio))
        new_width = max_size
    else:
        # If height is greater, set new height to max_size and scale width proportionally
        ratio = max_size / float(orig_height)
        new_width = int(float(orig_width) * float(ratio))
        new_height = max_size

    # Resize the image
    resized_image = image.resize((new_width, new_height))
    return resized_image
