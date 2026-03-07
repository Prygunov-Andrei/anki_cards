import io
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.image_generation import generate_scene_image
from apps.literary_context.models import SceneAnchor


def _mock_dalle_response(image_url='https://example.com/image.png'):
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.url = image_url
    mock_response.data = [mock_data]
    return mock_response


def _mock_image_bytes():
    """Create a minimal valid JPEG image."""
    from PIL import Image
    img = Image.new('RGB', (10, 10), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


class TestGenerateSceneImage:
    @patch('apps.literary_context.image_generation.requests.get')
    @patch('apps.literary_context.image_generation.get_openai_client')
    def test_generates_image(
        self, mock_client_fn, mock_requests_get, scene_anchor, settings_obj, tmp_path
    ):
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.images.generate.return_value = _mock_dalle_response()

            mock_img_response = MagicMock()
            mock_img_response.content = _mock_image_bytes()
            mock_img_response.raise_for_status = MagicMock()
            mock_requests_get.return_value = mock_img_response

            result = generate_scene_image(scene_anchor, settings_obj)

            assert result.startswith('literary_scenes/')
            assert result.endswith('.jpg')

            scene_anchor.refresh_from_db()
            assert scene_anchor.is_generated
            assert scene_anchor.image_prompt != ''
            assert str(scene_anchor.image_file).startswith('literary_scenes/')
        finally:
            django_settings.MEDIA_ROOT = original_media_root

    @patch('apps.literary_context.image_generation.requests.get')
    @patch('apps.literary_context.image_generation.get_openai_client')
    def test_prompt_includes_scene_description(
        self, mock_client_fn, mock_requests_get, scene_anchor, settings_obj, tmp_path
    ):
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.images.generate.return_value = _mock_dalle_response()

            mock_img_response = MagicMock()
            mock_img_response.content = _mock_image_bytes()
            mock_img_response.raise_for_status = MagicMock()
            mock_requests_get.return_value = mock_img_response

            generate_scene_image(scene_anchor, settings_obj)

            call_args = mock_client.images.generate.call_args
            prompt = call_args.kwargs['prompt']
            assert 'town square' in prompt.lower() or 'police' in prompt.lower()
        finally:
            django_settings.MEDIA_ROOT = original_media_root

    @patch('apps.literary_context.image_generation.requests.get')
    @patch('apps.literary_context.image_generation.get_openai_client')
    def test_shared_between_languages(
        self, mock_client_fn, mock_requests_get,
        scene_anchor, fragment_ru, fragment_de, settings_obj, tmp_path
    ):
        """Two fragments sharing same anchor = one image."""
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.images.generate.return_value = _mock_dalle_response()

            mock_img_response = MagicMock()
            mock_img_response.content = _mock_image_bytes()
            mock_img_response.raise_for_status = MagicMock()
            mock_requests_get.return_value = mock_img_response

            generate_scene_image(scene_anchor, settings_obj)

            # Both fragments share the same anchor image
            assert fragment_ru.anchor.id == scene_anchor.id
            assert fragment_de.anchor.id == scene_anchor.id

            scene_anchor.refresh_from_db()
            assert scene_anchor.image_file
            # Only one image generated
            assert mock_client.images.generate.call_count == 1
        finally:
            django_settings.MEDIA_ROOT = original_media_root


class TestGenerateSceneImagesCommand:
    @patch('apps.literary_context.image_generation.requests.get')
    @patch('apps.literary_context.image_generation.get_openai_client')
    def test_dry_run(self, mock_client_fn, mock_requests_get, scene_anchor, settings_obj):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command(
            'generate_scene_images',
            source_slug='chekhov',
            dry_run=True,
            stdout=out,
        )
        output = out.getvalue()
        assert 'Dry run' in output
        assert 'Prompt' in output
        mock_client_fn.assert_not_called()

    def test_missing_source(self, db):
        from django.core.management import call_command
        from io import StringIO

        err = StringIO()
        call_command('generate_scene_images', source_slug='nonexistent', stderr=err)
        assert 'not found' in err.getvalue()

    def test_no_anchors_needed(self, chekhov_source, settings_obj):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('generate_scene_images', source_slug='chekhov', stdout=out)
        assert 'No anchors' in out.getvalue()
