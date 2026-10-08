import cloudinary
import cloudinary.uploader
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class HelpdeskCloudinaryStorage(Storage):

    def _get_resource_type_from_name(self, name):
        name = name.lower()

        image_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
            ".svg",
        )

        video_extensions = (
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".mpeg",
            ".mpg",
        )

        if name.endswith(image_extensions):
            return "image"

        if name.endswith(video_extensions):
            return "video"

        return "raw"

    def _save(self, name, content):

        content_type = getattr(content, "content_type", "")

        if content_type.startswith("image/"):
            resource_type = "image"

        elif content_type.startswith("video/"):
            resource_type = "video"

        else:
            resource_type = self._get_resource_type_from_name(name)

        response = cloudinary.uploader.upload(
            content,
            folder="helpdesk/attachments",
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True,
        )

        return f"{resource_type}:{response['public_id']}"

    def url(self, name):

        if ":" in name:
            resource_type, public_id = name.split(":", 1)
        else:
            resource_type = self._get_resource_type_from_name(name)
            public_id = name

        return cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            type="upload",
            secure=True,
        )[0]

    def exists(self, name):
        return False

    def delete(self, name):
        pass