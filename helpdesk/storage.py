import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage


class HelpdeskCloudinaryStorage(MediaCloudinaryStorage):

    def _get_resource_type(self, content):
        """
        Decide how Cloudinary should store the file.

        Images -> image
        Videos -> video
        Other files -> raw
        """

        content_type = getattr(content, "content_type", None)

        if content_type:
            if content_type.startswith("image/"):
                return "image"

            if content_type.startswith("video/"):
                return "video"

        name = getattr(content, "name", "").lower()

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

    def _upload(self, name, content):
        """
        Upload the file to Cloudinary and return
        the COMPLETE Cloudinary response dictionary.
        """

        resource_type = self._get_resource_type(content)

        response = cloudinary.uploader.upload(
            content,
            folder="helpdesk/attachments",
            resource_type=resource_type,
            tags="media",
            use_filename=True,
        )

        # IMPORTANT:
        # Return the dictionary, NOT response["public_id"]
        return response