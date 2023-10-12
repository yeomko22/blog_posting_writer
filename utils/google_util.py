import io
import os
from datetime import datetime
from typing import List

import streamlit as st
from PIL import Image
from google.cloud import storage
from stqdm import stqdm
from streamlit.runtime.uploaded_file_manager import UploadedFile

from utils.image_util import resize_image

os.environ["GCLOUD_PROJECT"] = st.secrets["GCS_KEY"]["project_id"]


@st.cache_resource
def init_storage_client():
    return storage.Client.from_service_account_info(st.secrets["GCS_KEY"])


def upload_single_image(file_id: str, resized_buf: io.BytesIO) -> str:
    storage_client = init_storage_client()
    bucket_name = st.secrets["GCS_BUCKET"]
    bucket = storage_client.bucket(bucket_name)
    cur_datetime = datetime.now().strftime("%Y%m%d")
    destination_blob_name = f"blog_images/{cur_datetime}/{file_id}"
    blob = bucket.blob(destination_blob_name)
    if not blob.exists():
        blob.upload_from_string(resized_buf.getvalue())
    url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    return url


def upload_images(uploaded_files: List[UploadedFile]) -> List[str]:
    image_urls = []
    for i in stqdm(range(len(uploaded_files)), desc="이미지 업로드"):
        cur_file = uploaded_files[i]
        cur_file_id = cur_file.file_id
        cur_image = Image.open(cur_file)
        resized_image = resize_image(cur_image)
        resized_buf = io.BytesIO()
        resized_image.save(resized_buf, format="PNG")
        url = upload_single_image(cur_file_id, resized_buf)
        image_urls.append(url)
    return image_urls
