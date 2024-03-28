import pygame
import cairosvg
from jinja2 import Template
import os
import time
import io
import json
from pathlib import Path

# Path to your SVG and JSON files
svg_file_path = Path(__file__).parent.joinpath("test.svg")
json_file_path = Path(__file__).parent.joinpath("data.json")

# Initialize Pygame
pygame.init()
window_size = (400, 400)  # Adjust as per your SVG dimensions
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("SVG File Rendering in Pygame")


def load_data(json_path):
    # Read the JSON file
    with open(json_path, "r") as json_file:
        return json.load(json_file)


def load_and_render_svg(svg_path, data):
    # Read the SVG file
    with open(svg_path, "r") as svg_file:
        svg_template = svg_file.read()

    template = Template(svg_template)
    rendered_svg = template.render(**data)
    # Convert SVG string to a PNG image using CairoSVG
    png_image = cairosvg.svg2png(bytestring=rendered_svg.encode("utf-8"))
    # Convert PNG bytes to a Pygame surface
    png_io = io.BytesIO(png_image)
    return pygame.image.load(png_io)


# Load initial data
DATA = load_data(json_file_path)

# Initially load the SVG
pygame_image = load_and_render_svg(svg_file_path, DATA)
last_svg_mod_time = os.path.getmtime(svg_file_path)
last_json_mod_time = os.path.getmtime(json_file_path)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check for file modification
    current_svg_mod_time = os.path.getmtime(svg_file_path)
    current_json_mod_time = os.path.getmtime(json_file_path)

    if (
        current_svg_mod_time != last_svg_mod_time
        or current_json_mod_time != last_json_mod_time
    ):
        if current_json_mod_time != last_json_mod_time:
            DATA = load_data(json_file_path)
            last_json_mod_time = current_json_mod_time
        pygame_image = load_and_render_svg(svg_file_path, DATA)
        last_svg_mod_time = current_svg_mod_time

    window.fill((255, 255, 255))  # Fill background with white
    window.blit(pygame_image, (0, 0))  # Draw the image

    pygame.display.flip()
    time.sleep(0.1)  # Add slight delay to reduce CPU usage

pygame.quit()
