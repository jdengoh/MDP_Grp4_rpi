import os
import time
import glob
import shutil
from PIL import Image



def stitch_image():
    """
    Stitches the images in the folder together and saves it into runs/stitched folder
    """
    # Initialize path to save stitched image
    imgFolder = 'runs'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    # Find all files that ends with ".jpg" (this won't match the stitched images as we name them ".jpeg")
    imgPaths = glob.glob(os.path.join(imgFolder+"/detect/*/", "*.jpg"))
    # Open all images
    images = [Image.open(x) for x in imgPaths]
    # Get the width and height of each image
    width, height = zip(*(i.size for i in images))
    # Calculate the total width and max height of the stitched image, as we are stitching horizontally
    total_width = sum(width)
    max_height = max(height)
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0

    # Stitch the images together
    for im in images:
        stitchedImg.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    # Save the stitched image to the path
    stitchedImg.save(stitchedPath)

    # Move original images to "originals" subdirectory
    for img in imgPaths:
        shutil.move(img, os.path.join(
            "runs", "originals", os.path.basename(img)))

    return stitchedImg

def stitch_image_own():
    """
    Stitches the images in the folder together and saves it into own_results folder

    Basically similar to stitch_image() but with different folder names and slightly different drawing of bounding boxes and text
    """
    imgFolder = 'own_results'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    imgPaths = glob.glob(os.path.join(imgFolder+"/annotated_image_*.jpg"))
    imgTimestamps = [imgPath.split("_")[-1][:-4] for imgPath in imgPaths]
    
    sortedByTimeStampImages = sorted(zip(imgPaths, imgTimestamps), key=lambda x: x[1])

    images = [Image.open(x[0]) for x in sortedByTimeStampImages]
    width, height = zip(*(i.size for i in images))
    total_width = sum(width)
    max_height = max(height)
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0

    for im in images:
        stitchedImg.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    stitchedImg.save(stitchedPath)

    return stitchedImg

def stitch_image_in_two_rows():
    """
    Stitches the images in the folder together and divides them between 2 rows.
    Saves it into runs/stitched folder.
    """
    # Initialize path to save stitched image
    imgFolder = 'runs'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    # Find all files that ends with ".jpg" (this won't match the stitched images as we name them ".jpeg")
    imgPaths = glob.glob(os.path.join(imgFolder+"/detect/*/", "*.jpg"))
    
    # Open all images
    images = [Image.open(x) for x in imgPaths]
    
    # Calculate the number of images per row
    num_images = len(images)
    half = num_images // 2 if num_images % 2 == 0 else (num_images // 2) + 1
    
    # Split the images into two rows
    first_row_images = images[:half]
    second_row_images = images[half:]
    
    # Get the width and height of each image
    first_row_widths, first_row_heights = zip(*(i.size for i in first_row_images))
    second_row_widths, second_row_heights = zip(*(i.size for i in second_row_images))
    
    # Calculate the total width and max height for both rows
    max_width_first_row = sum(first_row_widths)
    max_width_second_row = sum(second_row_widths)
    
    total_width = max(max_width_first_row, max_width_second_row)
    total_height = max(first_row_heights) + max(second_row_heights)  # Combine heights of both rows
    
    # Create a new image with the total width and height of both rows
    stitchedImg = Image.new('RGB', (total_width, total_height))
    
    # Stitch the first row of images
    x_offset = 0
    for im in first_row_images:
        stitchedImg.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    
    # Stitch the second row of images
    x_offset = 0
    for im in second_row_images:
        stitchedImg.paste(im, (x_offset, max(first_row_heights)))
        x_offset += im.size[0]
    
    # Save the stitched image to the path
    stitchedImg.save(stitchedPath)

    return stitchedImg


stitch_image_in_two_rows()