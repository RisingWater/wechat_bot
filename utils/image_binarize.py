import cv2
import numpy as np
import logging
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class ImageBinarrize:
    def __init__(self):
        """初始化文件识别器"""
    def remove_shadows_simple_contrast(self, img_path, kernel_size=501, contrast=1.8, brightness=0):
        """
        去除阴影并直接调整对比度
        Args:
            img_path: 输入图像路径
            kernel_size: 模糊核大小
            contrast: 对比度因子 (1.5-2.5)
            brightness: 亮度调整 (-50 到 50)
        Returns:
            result: 最终处理结果
            shadow_removed: 仅去阴影未调对比度的图像
            original: 原图
        """
        # 读取图像
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图像: {img_path}")
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_float = gray.astype(np.float32)
        
        # 去除阴影
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        background = cv2.GaussianBlur(gray_float, (kernel_size, kernel_size), 0)
        divided = gray_float / (background + 1e-7)
        normalized = cv2.normalize(divided, None, 0, 255, cv2.NORM_MINMAX)
        shadow_removed = normalized.astype(np.uint8)
        
        # 直接调整对比度和亮度
        result = cv2.convertScaleAbs(shadow_removed, alpha=contrast, beta=brightness)
        
        return result, shadow_removed, gray

    def binarize_image(self, image, threshold=127, invert=False):
        """
        对图像进行二值化处理
        Args:
            image: 输入图像（灰度图）
            threshold: 阈值 (0-255)
            invert: 是否反转（True: 白底黑字, False: 黑底白字）
        Returns:
            binary: 二值化图像
        """
        if invert:
            # 白底黑字：大于阈值的变为0（黑色），小于等于的变为255（白色）
            _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
        else:
            # 黑底白字：大于阈值的变为255（白色），小于等于的变为0（黑色）
            _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        
        return binary

    def adaptive_binarize_better(self, image, block_size=31, C=10, method='gaussian', invert=False):
        """
        改进的自适应二值化
        Args:
            block_size: 邻域大小，建议15-51的奇数
            C: 从均值减去的常数，建议5-15
            method: 'gaussian' 或 'mean'
            invert: True为白底黑字
        """
        if block_size % 2 == 0:
            block_size += 1
        
        if method == 'gaussian':
            adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        else:
            adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
        
        if invert:
            binary = cv2.adaptiveThreshold(image, 255, adaptive_method, 
                                        cv2.THRESH_BINARY_INV, block_size, C)
        else:
            binary = cv2.adaptiveThreshold(image, 255, adaptive_method, 
                                        cv2.THRESH_BINARY, block_size, C)
        return binary

    def process_pipeline(self, img_path, 
                        kernel_size=601, 
                        contrast=2.0, 
                        brightness=10,
                        binarize=True,
                        threshold=160,
                        invert=False):
        """
        完整的处理流程：去阴影 -> 对比度增强 -> 二值化
        Args:
            img_path: 输入图像路径
            kernel_size: 去阴影核大小
            contrast: 对比度
            brightness: 亮度
            binarize: 是否进行二值化
            threshold: 二值化阈值
            use_adaptive: 是否使用自适应二值化
            invert: 是否反转（True: 白底黑字）
        Returns:
            final_result: 最终结果
            enhanced: 增强后的图像（未二值化）
        """
        # 1. 去阴影和对比度增强
        enhanced, shadow_removed, original = self.remove_shadows_simple_contrast(
            img_path, kernel_size, contrast, brightness
        )
        
        final_result = enhanced
        
        # 2. 二值化（如果需要）
        if binarize:
            final_result = self.binarize_image(enhanced, threshold, invert)
            #final_result = adaptive_binarize_better(enhanced, invert=invert)
        
        return final_result, enhanced

    def process_image(self, input_path, output_path):
        final_result, enhanced = self.process_pipeline(
            input_path,
            kernel_size=601,
            contrast=2.0,
            brightness=10,
            binarize=True,
            threshold=192,  # 可以调整这个阈值
            invert=False     # 白底黑字
        )

        cv2.imwrite(output_path, final_result)

# 主函数
def main():
    img_path = [
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg"
    ]
    
    print("=== 文档阴影去除与对比度增强 ===\n")

    image = ImageBinarrize()

    for input_path in img_path:
        output_path = "out_" + input_path
        ImageBinarrize.process_image(input_path, output_path)

    print("\n处理完成！")

if __name__ == "__main__":
    main()