#!/usr/bin/env python3
import pypandoc
import requests
import os
import sys
import logging
from bs4 import BeautifulSoup
import tempfile
import re
import base64
import urllib.parse
from docx import Document

logger = logging.getLogger(__name__)

class FixedWebConverter:
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
        self.base_url = None
    
    def setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def download_image(self, img_url):
        """下载图片并转换为base64"""
        try:
            # 处理相对URL
            if not img_url.startswith('http'):
                if self.base_url:
                    img_url = urllib.parse.urljoin(self.base_url, img_url)
                else:
                    return None
            
            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()
            
            # 转换为base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            
            # 获取图片类型
            content_type = response.headers.get('content-type', 'image/jpeg')
            if content_type == 'image/jpeg':
                data_uri = f"data:image/jpeg;base64,{image_data}"
            elif content_type == 'image/png':
                data_uri = f"data:image/png;base64,{image_data}"
            elif content_type == 'image/gif':
                data_uri = f"data:image/gif;base64,{image_data}"
            else:
                data_uri = f"data:{content_type};base64,{image_data}"
            
            return data_uri
            
        except Exception as e:
            logger.warning(f"下载图片失败 {img_url}: {e}")
            return None
    def fetch_and_clean_html(self, url):
        """获取并清理HTML内容，处理图片"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            self.base_url = url
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 获取网页标题 - 优先使用 og:title，如果没有则使用 title 标签
            page_title = "无标题"
            
            # 1. 首先检查 og:title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                page_title = og_title['content'].strip()
            else:
                # 2. 如果没有 og:title，使用标准的 title 标签
                title_tag = soup.find('title')
                if title_tag and title_tag.get_text():
                    page_title = title_tag.get_text().strip()
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
    
            # 处理图片 - 下载并替换为base64
            for img in soup.find_all('img'):
                img_src = img.get('src')
                if not img_src:
                    img_src = img.get('data-src')

                if img_src:
                    data_uri = self.download_image(img_src)
                    print(f"正在处理图片src: {img_src}")
                    if data_uri:
                        img['src'] = data_uri
                        logger.info(f"已嵌入图片: {img_src}")
                    else:
                        # 如果下载失败，保留原始链接
                        if not img_src.startswith('http') and self.base_url:
                            img['src'] = urllib.parse.urljoin(self.base_url, img_src)

            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            cleaned_html = str(main_content)
            
            # 返回两个值：清理后的HTML和网页标题
            return cleaned_html, page_title
            
        except Exception as e:
            logger.error(f"获取或清理HTML失败: {e}")
            raise
    
    def convert_html_to_docx(self, html_content, output_path):
        """使用pandoc转换HTML到DOCX（修复参数）"""
        
        # 使用新的参数替代 --self-contained
        extra_args = [
            '--standalone',
            '--embed-resources',      # 替代 --self-contained
            '--toc-depth=3',
        ]
        
        try:
            pypandoc.convert_text(
                source=html_content,
                to='docx',
                format='html',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            logger.info(f"转换成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"pandoc转换失败: {e}")
            return False
    
    def paragraph_has_picture(self, paragraph):
        """调试文档结构（包含图片检测）"""
        from docx.oxml.ns import qn

        for run in paragraph.runs:
            # 方法1：检查 drawing 元素
            drawings = run._element.findall('.//' + qn('w:drawing'))
            if drawings:
                print("paragraph.picture: w:drawing")
                return True
            
            # 方法2：检查 graphic 元素
            graphics = run._element.findall('.//' + qn('a:graphic'))
            if graphics:
                print("paragraph.picture: w:graphic")
                return True
            
            # 方法3：直接查找 blip 元素（图片引用）
            blips = run._element.findall('.//' + qn('a:blip'))
            if blips:
                print("paragraph.picture: w:blip")
                return True

        return False
    
    def remove_empty_paragraphs(self, docx_path):
        """移除DOCX文件中的空段落（非常安全，确保不删除任何有内容的段落）"""
        try:
            # 打开文档
            doc = Document(docx_path)
            
            # 找出所有空段落
            empty_paragraphs = []
            for paragraph in doc.paragraphs:
                # 严格检查：段落必须完全没有任何内容
                # 没有文本 并且 没有runs 或者 所有runs都是空的
                text_empty = not paragraph.text.strip()
                # print("paragraph.text: ", paragraph.text.strip())
                runs_empty = not self.paragraph_has_picture(paragraph)
                # print("paragraph.picture: ", runs_empty)
                
                if text_empty and runs_empty:
                    empty_paragraphs.append(paragraph)
            
            # 移除空段落（需要反向遍历）
            for paragraph in reversed(empty_paragraphs):
                p = paragraph._element
                p.getparent().remove(p)
            
            # 保存文档
            doc.save(docx_path)
            logger.info(f"已移除 {len(empty_paragraphs)} 个空段落")
            return True
            
        except Exception as e:
            logger.error(f"清理空段落失败: {e}")
            return False

    def convert_url_to_docx(self, url, output_dir):
        """主转换函数"""
        try:
            logger.info("正在获取和清理网页内容...")
            html_content, html_title = self.fetch_and_clean_html(url)

            safe_title = re.sub(r'[<>:"/\\|?*]', '', html_title)
            safe_title = safe_title.replace(' ', '_')  # 空格替换为下划线

            output_path = os.path.join(output_dir, f"{safe_title}.docx")
            
            logger.info("正在转换为DOCX...")
            success = self.convert_html_to_docx(html_content, output_path)
            if not success:
                return None
            
            self.remove_empty_paragraphs(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"转换过程失败: {e}")
            return None
    
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='修复版网页转DOCX工具')
    parser.add_argument('url', help='网页URL')
    parser.add_argument('-o', '--output', help='输出DOCX文件路径', default='output.docx')
    
    args = parser.parse_args()
    
    converter = FixedWebConverter()
    success = converter.convert_url_to_docx(args.url, args.output)
    
    if success:
        logger.info(f"🎉 转换完成！文件保存在: {os.path.abspath(args.output)}")
    else:
        logger.error("❌ 转换失败")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()