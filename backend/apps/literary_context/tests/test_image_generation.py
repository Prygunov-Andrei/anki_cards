import io
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.image_generation import generate_scene_image
from apps.literary_context.models import SceneAnchor


def _mock_image_bytes():
    """Create a minimal valid JPEG image."""
    from PIL import Image
    img = Image.new('RGB', (10, 10), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


def _mock_gemini_response(image_data):
    """Create a mock Gemini response with inline image data."""
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = image_data
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    return mock_response


class TestGenerateSceneImage:
    @patch('google.generativeai.GenerativeModel')
    @patch('apps.core.llm.clients.get_gemini_client')
    def test_generates_image_with_gemini(
        self, mock_client_fn, mock_model_cls, scene_anchor, settings_obj, tmp_path
    ):
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            image_data = _mock_image_bytes()
            mock_model = MagicMock()
            mock_model_cls.return_value = mock_model
            mock_model.generate_content.return_value = _mock_gemini_response(image_data)

            result = generate_scene_image(scene_anchor, settings_obj)

            assert result.startswith('literary_scenes/')
            assert result.endswith('.jpg')

            scene_anchor.refresh_from_db()
            assert scene_anchor.is_generated
            assert scene_anchor.image_prompt != ''

            # Verify correct model used
            mock_model_cls.assert_called_with('gemini-3.1-flash-image-preview')
        finally:
            django_settings.MEDIA_ROOT = original_media_root

    @patch('google.generativeai.GenerativeModel')
    @patch('apps.core.llm.clients.get_gemini_client')
    def test_prompt_includes_scene_description(
        self, mock_client_fn, mock_model_cls, scene_anchor, settings_obj, tmp_path
    ):
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            image_data = _mock_image_bytes()
            mock_model = MagicMock()
            mock_model_cls.return_value = mock_model
            mock_model.generate_content.return_value = _mock_gemini_response(image_data)

            generate_scene_image(scene_anchor, settings_obj)

            call_args = mock_model.generate_content.call_args
            prompt = call_args[0][0]
            assert 'town square' in prompt.lower() or 'police' in prompt.lower()
        finally:
            django_settings.MEDIA_ROOT = original_media_root

    @patch('google.generativeai.GenerativeModel')
    @patch('apps.core.llm.clients.get_gemini_client')
    def test_no_image_in_response_raises(
        self, mock_client_fn, mock_model_cls, scene_anchor, settings_obj, tmp_path
    ):
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            mock_model = MagicMock()
            mock_model_cls.return_value = mock_model
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = None
            mock_part.image = None
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].content.parts = [mock_part]
            mock_model.generate_content.return_value = mock_response

            with pytest.raises(Exception, match='Could not extract image'):
                generate_scene_image(scene_anchor, settings_obj)
        finally:
            django_settings.MEDIA_ROOT = original_media_root

    @patch('google.generativeai.GenerativeModel')
    @patch('apps.core.llm.clients.get_gemini_client')
    def test_shared_between_languages(
        self, mock_client_fn, mock_model_cls,
        scene_anchor, fragment_ru, fragment_de, settings_obj, tmp_path
    ):
        """Two fragments sharing same anchor = one image."""
        from django.conf import settings as django_settings
        original_media_root = django_settings.MEDIA_ROOT
        django_settings.MEDIA_ROOT = str(tmp_path)

        try:
            image_data = _mock_image_bytes()
            mock_model = MagicMock()
            mock_model_cls.return_value = mock_model
            mock_model.generate_content.return_value = _mock_gemini_response(image_data)

            generate_scene_image(scene_anchor, settings_obj)

            assert fragment_ru.anchor.id == scene_anchor.id
            assert fragment_de.anchor.id == scene_anchor.id

            scene_anchor.refresh_from_db()
            assert scene_anchor.image_file
            assert mock_model.generate_content.call_count == 1
        finally:
            django_settings.MEDIA_ROOT = original_media_root


class TestGenerateSceneImagesCommand:
    @patch('google.generativeai.GenerativeModel')
    @patch('apps.core.llm.clients.get_gemini_client')
    def test_dry_run(self, mock_client_fn, mock_model_cls, scene_anchor, settings_obj):
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
        mock_model_cls.assert_not_called()

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
