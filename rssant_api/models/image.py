import typing
from urllib.parse import urlparse
from .helper import Model, models, optional


class ImageInfo(Model):
    """
    Image info for detact anti-stealing-link and auto image proxy.
    """

    class Meta:
        indexes = [
            models.Index(fields=["url_root", "dt_created"]),
        ]

    class Admin:
        display_fields = ['url_root']

    url_root = models.CharField(
        max_length=120, help_text="eg: https://image.example.com/root-path")
    sample_url = models.TextField(
        **optional, help_text='sample image url')
    user_agent = models.TextField(
        **optional, help_text="the user-agent used to request sample image")
    referer = models.TextField(
        **optional, help_text="the referer used to request sample image")
    status_code = models.IntegerField(
        **optional, help_text="the response status code when request sample image")
    dt_created = models.DateTimeField(auto_now_add=True, help_text="created datatime")

    @classmethod
    def batch_detect(cls, url_roots: typing.List[str]) -> dict:
        sql = """
        SELECT DISTINCT ON (url_root)
            id, url_root, status_code
        FROM rssant_api_imageinfo
        WHERE url_root = ANY(%s) AND status_code > 0
        ORDER BY url_root, dt_created DESC
        """
        url_root_map = {}
        rows = cls.objects.raw(sql, [list(url_roots)])
        for row in rows:
            url_root_map[row.url_root] = row.status_code
        return url_root_map

    @classmethod
    def extract_url_root(cls, url: str) -> str:
        """
        >>> url = 'https://image.example.com/root-path/123.png?key=value'
        >>> print(ImageInfo.extract_url_root(url))
        https://image.example.com/root-path
        >>> url = 'https://image.example.com/123.png?key=value'
        >>> print(ImageInfo.extract_url_root(url))
        https://image.example.com
        """
        p = urlparse(url)
        p.scheme, p.netloc, p.path
        scheme = p.scheme or 'http'
        path = (p.path or '').strip('/')
        parts = path.split('/', maxsplit=1)
        if len(parts) >= 2:
            root_path = '/' + parts[0]
        else:
            root_path = ''
        url_root = f'{scheme}://{p.netloc}{root_path}'
        return url_root

    @classmethod
    def batch_detect_images(cls, image_urls: typing.List[str]) -> dict:
        url_roots = set()
        image_url_maps = {}
        for url in image_urls:
            url_root = cls.extract_url_root(url)
            url_roots.add(url_root)
            image_url_maps[url] = url_root
        url_root_map = cls.batch_detect(url_roots)
        result = {}
        for image_url, url_root in image_url_maps.items():
            status_code = url_root_map.get(url_root)
            if status_code is not None:
                result[image_url] = status_code
        return result
