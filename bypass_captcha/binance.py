from typing import Tuple
from copy import deepcopy

import cv2
import numpy as np

class PreprocessImage:
    def process_image(self, str_img, piece_width = 60):
        image = self._convert_str_img_to_cv2_img(str_img)
        # self._save_img(image)
        piece, picture, piece_gray, picture_gray, y_0, y, piece_width = self._split_image(image, piece_width=piece_width)
        return image, piece, picture, piece_gray, picture_gray, y_0, y, piece_width
        
    def _convert_str_img_to_cv2_img(self, img_str) -> np.ndarray:
        nparr = np.frombuffer(img_str, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _save_img(self, image: np.ndarray):
        from datetime import datetime, timedelta
        current = (datetime.utcnow() + timedelta(hours=7)).strftime('%Y-%m-%d_%H:%M:%S')
        filename = f"captcha/{current}.png"
        cv2.imwrite(filename, image)
        
    def _split_image(self, image, piece_width = 60) -> Tuple[np.ndarray, np.ndarray, int]:
        height, width, channels = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) # convert into gray
        sobel_img = self._sobel_operator(gray)
        
        
        piece_background_color = self._get_background_of_piece(gray)
        if piece_width is None:
            piece_width = self._get_piece_width(sobel_img, piece_background_color)
        piece_gray = gray[:, 0:piece_width]
        picture_gray = gray[:, piece_width+1:]
        
        piece_gray, y_0, y = self._crop_piece(piece_gray, piece_background_color)
        
        piece = image[:, 0:piece_width]
        piece = piece[y_0:y_0+y, :]
        picture = image[:, piece_width+1:]
        return piece, picture, piece_gray, picture_gray, y_0, y, piece_width
    
    def _sobel_operator(self, gray_image: np.ndarray):
        img = deepcopy(gray_image)
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S

        img = cv2.GaussianBlur(img, (3, 3), 0)
        grad_x = cv2.Sobel(img, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(img, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

        return grad
    
    def _get_background_of_piece(self, image: np.ndarray) -> str:
        height, width = image.shape
        colors = {}
        for y in range(0, height):
            color = image[y][0]
            if color not in colors:
                colors[color] = 1
            else:
                colors[color] += 1
        colors = sorted(colors.items(), key=lambda item: item[1], reverse=True)
        color, _ = colors[0]
        return color
    
    def _get_piece_width(self, image: np.ndarray, piece_background_color: str) -> int:
        height, width = image.shape
        piece_width = 0
        for y in range(height):
            num = 0
            for x in range(width):
                color = image[y][x]
                if piece_background_color == color:
                    num += 1
                else:
                    break
            piece_width = max(piece_width, num)
        return piece_width
    
    def _crop_piece(self, piece_img: np.ndarray, piece_background_color: str) -> Tuple[np.ndarray, int]:
        height, width = piece_img.shape
        # crop top
        max_heigh = 0
        for y in range(height):
            num = 0
            for x in range(width):
                color = piece_img[y][x]
                if piece_background_color == color:
                    num += 1
            if num / width > 0.95:
                max_heigh += 1
            else:
                break
        piece_img = piece_img[max_heigh+1:, :]

        # crop bottom
        height, width = piece_img.shape
        max_heigh2 = height
        for y in range(height, 0, -1):
            num = 0
            for x in range(width, 0, -1):
                color = piece_img[y-1][x-1]
                if piece_background_color == color:
                    num += 1
            if num / width > 0.95:
                max_heigh2 -= 1
            else:
                break
        
        piece_img = piece_img[:max_heigh2, :]
        height, width = piece_img.shape
        return piece_img, max_heigh, height

class PuzleSolver:
    def get_position(self, str_img):
        preprocessor = PreprocessImage()
        image, piece, picture, piece_gray, picture_gray, y_0, y, piece_width = preprocessor.process_image(str_img, piece_width=60)
        pixels_extension = 0
        
        piece_gray2 = cv2.copyMakeBorder(piece_gray, pixels_extension, pixels_extension, pixels_extension, pixels_extension, cv2.BORDER_CONSTANT, None, 0)
        
        piece_gray2 = self._piece_preprocessing(piece_gray, pixels_extension)
        ppicture_gray2 = self._background_preprocessing(picture_gray, pixels_extension)
        
        res = cv2.matchTemplate(ppicture_gray2, piece_gray2, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        end = top_left[0] + pixels_extension 
        return end

    def _piece_preprocessing(self, piece_img: np.ndarray, pixels_extension: int):
        preprocessor = PreprocessImage()
        img = preprocessor._sobel_operator(piece_img)
        img = cv2.copyMakeBorder(img, pixels_extension, pixels_extension, pixels_extension, pixels_extension, cv2.BORDER_CONSTANT, None, 0)
        return img
        
    def _background_preprocessing(self, picture: np.ndarray, pixels_extension: int):
        preprocessor = PreprocessImage()
        img = preprocessor._sobel_operator(picture)
        img = cv2.copyMakeBorder(img, pixels_extension, pixels_extension, pixels_extension, pixels_extension, cv2.BORDER_CONSTANT, None, 0)
        return img
