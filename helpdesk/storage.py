
import os

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class HelpdeskCloudinaryStorage(Storage):

    def _save(self, name, content):
        # Ensure the file is read from the beginning.
        if hasattr(content, "seek"):
            content.seek(0)

        # Let Cloudinary determine whether the upload is an
        # image, video, or raw file.
        response = cloudinary.uploader.upload(
            content,
            resource_type="auto",
            folder="helpdesk/attachments",
            use_filename=True,
            unique_filename=True,
        )

        resource_type = response["resource_type"]
        public_id = response["public_id"]

        # Store the actual resource type returned by Cloudinary.
        return f"{resource_type}:{public_id}"

    def url(self, name):
        if ":" in name:
            resource_type, public_id = name.split(":", 1)
        else:
            resource_type = "raw"
            public_id = name

        return cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            type="upload",
            secure=True,
        )[0]

    def exists(self, name):
        # Cloudinary generates unique filenames for uploads.
        return False

    def delete(self, name):
        # Deletion can be implemented separately if required.
        pass

