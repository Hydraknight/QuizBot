import sys
import json
from PIL import Image, ImageDraw, ImageFont


def generate_matrix(answer_matrix, output_path):
    """
    Generates a matrix image showing correct and wrong answers for each team.

    :param answer_matrix: A dictionary where keys are team names and values are lists of 1s (correct) and 0s (wrong)
    :param output_path: Path to save the generated image
    :param font_path: Path to the font file for the title and labels
    """
    # Parameters
    cell_size = 40
    correct_color = (104, 255, 97)  # Pastel green
    wrong_color = (255, 102, 103)   # Pastel red
    text_color = (255, 255, 255)    # White
    bg_color = (0, 0, 0)            # Black
    padding = 20
    # Load the font
    font_path = "font.ttf"
    font = ImageFont.truetype(font_path, 20)
    title_font = ImageFont.truetype(font_path, 30)

    # Initial dimensions to calculate title width and longest team name width
    temp_image = Image.new('RGB', (1, 1), color=bg_color)
    temp_draw = ImageDraw.Draw(temp_image)

    # Calculate title dimensions
    title = "Answer Matrix"
    title_bbox = temp_draw.textbbox((0, 0), title, font=title_font)
    title_width, title_height = title_bbox[2] - \
        title_bbox[0], title_bbox[3] - title_bbox[1]

    # Calculate the width of the longest team name
    longest_team_name = max(answer_matrix.keys(), key=lambda name: temp_draw.textbbox(
        (0, 0), name, font=font)[2] - temp_draw.textbbox((0, 0), name, font=font)[0])
    longest_team_name_width = temp_draw.textbbox((0, 0), longest_team_name, font=font)[
        2] - temp_draw.textbbox((0, 0), longest_team_name, font=font)[0]

    # Matrix dimensions
    num_teams = len(answer_matrix)
    num_questions = max(len(answers) for answers in answer_matrix.values())
    matrix_width = num_questions * cell_size
    matrix_height = num_teams * cell_size

    # Calculate image dimensions
    image_width = max(title_width, matrix_width +
                      longest_team_name_width + padding) + 2 * padding
    image_height = title_height + matrix_height + 3 * \
        cell_size  # 3 cells for padding and labels

    # Calculate starting positions to center the matrix
    matrix_x_start = (image_width - matrix_width - longest_team_name_width -
                      padding) / 2 + longest_team_name_width + padding
    matrix_y_start = title_height + 2.5 * cell_size

    # Create the final image
    image = Image.new('RGB', (image_width, image_height), color=bg_color)
    draw = ImageDraw.Draw(image)

    # Draw the title
    title_x = (image_width - title_width) / 2
    draw.text((title_x, padding), title, fill=text_color, font=title_font)

    # Draw the labels for x and y axes
    for j in range(num_questions):
        label = f"Q{j + 1}"
        label_bbox = draw.textbbox((0, 0), label, font=font)
        label_width, label_height = label_bbox[2] - \
            label_bbox[0], label_bbox[3] - label_bbox[1]
        label_x = matrix_x_start + (j * cell_size) + \
            (cell_size - label_width) / 2
        draw.text((label_x, title_height + 1.5 * cell_size),
                  label, fill=text_color, font=font)

    for i, team in enumerate(answer_matrix.keys()):
        label = team
        label_bbox = draw.textbbox((0, 0), label, font=font)
        label_width, label_height = label_bbox[2] - \
            label_bbox[0], label_bbox[3] - label_bbox[1]
        label_x = matrix_x_start - padding - label_width
        label_y = matrix_y_start + (i * cell_size) + \
            (cell_size - label_height) / 2
        draw.text((label_x, label_y), label, fill=text_color, font=font)

    # Draw the matrix
    for i, (team, answers) in enumerate(answer_matrix.items()):
        for j, answer in enumerate(answers):
            color = correct_color if answer == 1 else wrong_color
            top_left = (matrix_x_start + j * cell_size,
                        matrix_y_start + i * cell_size)
            bottom_right = (top_left[0] + cell_size, top_left[1] + cell_size)
            draw.rectangle([top_left, bottom_right],
                           fill=color, outline=text_color)

    # Save the image
    image.save(output_path)


if __name__ == "__main__":
    answer_matrix = json.loads(sys.argv[1])
    output_path = sys.argv[2]
    font_path = sys.argv[3]
    generate_matrix(answer_matrix, output_path, font_path)
