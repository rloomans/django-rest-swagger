from unittest import TestCase

import simplejson as json
from rest_framework_swagger.renderers import SwaggerUIRenderer

from ..compat.mock import patch, MagicMock


class TestSwaggerUIRenderer(TestCase):
    def setUp(self):
        self.sut = SwaggerUIRenderer()
        self.renderer_context = {'request': MagicMock()}

        swagger_settings_patcher = patch(
            'rest_framework_swagger.renderers.swagger_settings',
        )
        self.swagger_settings = swagger_settings_patcher.start()
        self.addCleanup(swagger_settings_patcher.stop)

    def test_media_type(self):
        self.assertEqual('text/html', self.sut.media_type)

    def test_format(self):
        self.assertEqual('swagger', self.sut.format)

    def test_template(self):
        self.assertEqual(
            'rest_framework_swagger/index.html',
            self.sut.template
        )

    def test_charset(self):
        self.assertEqual('utf-8', self.sut.charset)

    @patch('rest_framework_swagger.renderers.render')
    def test_render(self, render_mock):
        with patch.object(self.sut, 'set_context') as context_mock:
            self.sut.render(
                data=None,
                accepted_media_type=None,
                renderer_context=self.renderer_context
            )

        context_mock.assert_called_once_with(self.renderer_context)
        render_mock.assert_called_once_with(
            self.renderer_context['request'],
            self.sut.template,
            self.renderer_context
        )

    def test_set_context_use_session_auth(self):
        self.sut.set_context(self.renderer_context)

        self.assertEqual(
            self.renderer_context['USE_SESSION_AUTH'],
            self.swagger_settings.USE_SESSION_AUTH
        )

    def test_set_context_sets_auth_urls(self):
        urls = {'fizz': 'buzz'}
        with patch.object(self.sut, 'get_auth_urls', return_value=urls):
            self.sut.set_context(self.renderer_context)

        self.assertDictContainsSubset(urls, self.renderer_context)

    def test_set_context_sets_ui_esttings(self):
        with patch.object(self.sut, 'get_ui_settings') as mock:
            mock.return_value = {'foo': 'bar'}
            self.sut.set_context(self.renderer_context)

        self.assertEqual(
            json.dumps(mock.return_value),
            self.renderer_context['drs_settings']
        )

    def test_get_auth_urls(self):
        key = 'LOGIN_URL'
        value = '/foo?next=bar'
        with patch.multiple(
            self.sut,
            get_auth_url_settings=lambda *args: {key: ''},
            add_next_to_url=lambda *args: value
        ):
            self.sut.set_context(self.renderer_context)

        self.assertDictContainsSubset({key: value}, self.renderer_context)

    def test_get_auth_url_settings(self):
        self.assertDictEqual(
            {
                'LOGIN_URL': self.swagger_settings.LOGIN_URL,
                'LOGOUT_URL': self.swagger_settings.LOGOUT_URL
            },
            self.sut.get_auth_url_settings()
        )

    def test_get_ui_settings_without_validator_url(self):
        expected = {
            'apisSorter': self.swagger_settings.APIS_SORTER,
            'docExpansion': self.swagger_settings.DOC_EXPANSION,
            'jsonEditor': self.swagger_settings.JSON_EDITOR,
            'operationsSorter': self.swagger_settings.OPERATIONS_SORTER,
            'showRequestHeaders': self.swagger_settings.SHOW_REQUEST_HEADERS,
            'supportedSubmitMethods':
            self.swagger_settings.SUPPORTED_SUBMIT_METHODS,
            'validatorUrl': self.swagger_settings.VALIDATOR_URL
        }
        result = self.sut.get_ui_settings()

        self.assertDictEqual(expected, result)

    def test_validator_url_none_when_set(self):
        self.swagger_settings.VALIDATOR_URL = None
        result = self.sut.get_ui_settings()

        self.assertDictContainsSubset({'validatorUrl': None}, result)

    def test_validator_url_not_present_when_empty_string(self):
        """
        Given the validator URL is unspecified (empty string, not null),
        the validatorUrl should not be present. SwaggerUI will use
        swagger.io as the default.
        """
        self.swagger_settings.VALIDATOR_URL = ''
        result = self.sut.get_ui_settings()

        self.assertNotIn('validatorUrl', result)

    @patch('rest_framework_swagger.renderers.resolve_url')
    def test_add_next_to_url(self, mock):
        request = MagicMock(path='industries')
        url = '/vandelay'
        expected = '%s?next=%s' % (mock.return_value, request.path)

        self.assertEqual(expected, self.sut.add_next_to_url(url, request))
        mock.assert_called_once_with(url)
