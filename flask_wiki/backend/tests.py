import os
from flask import url_for
from flask.ext.testing import TestCase
from flask_wiki.backend.models import Page
from flask_wiki.backend.backend import db, mixer, app
from flask_wiki.backend.serialization_fields import GUIDSerializationField
from slugify import slugify

os.environ['CONFIG_MODULE'] = 'config.test'


class BackendTestCase(TestCase):
    """
    Test all Backend API EndPoints.
    """
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        return app

    def setUp(self, **kwargs):
        # Create a temp database and create an Page Object.
        db.create_all()
        self.page = mixer.blend(Page)

    def tearDown(self):
        # TODO: FUCKING TRASH USING PRODUCTION DB.
        db.session.remove()
        db.drop_all()

    def test_get_list_of_pages(self):
        response = self.client.get(url_for('pages-list'))
        # Can we Find the Main Page in the response?
        self.assertIn(self.page.name, str(response.data))

        # Can we find a GUID key.
        self.assertIn('guid', str(response.data))

        # The Guid is Valid?
        # Testing Customized Serialization Field
        result = GUIDSerializationField().deserialize(response.json[0]['guid'])
        self.assertTrue(result)

    def test_create_new_page(self):
        # Try to create a New page using the API.
        # TODO: Headers are not working with flask testing. Verify.
        # header={"Content-Type": "application/json"}
        url = url_for('pages-list')

        data = {
            "name": "Unittest Page",
            "raw_content": "My Title\n====="
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 201)

        # Verify if the correct HTML for Markdown was returned
        self.assertIn('<h1>My Title</h1>', str(response.data))

        # Try to submit the same data again, a 422 code is expected
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 422)

    def test_get_specific_page(self):
        # Try to look for a specific page.
        slug = slugify(self.page.name)
        url = url_for('page-detail', slug=slug)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Find the raw_content of the page.
        self.assertIn(self.page.raw_content, str(response.data))

    def test_patch_existing_page(self):
        # Try to update a existing resource.
        url = url_for('page-detail', slug='unittest-page')

        data = {
            "raw_content": "UnitTest\n=======",
        }
        # TODO: Verify why the response is 200 but in browser
        # it returns 204 correctly.
        response = self.client.patch(url, data=data)

        self.fail('The test cant find the specified page for now. '
                  'Browser is working.')
        self.assertEqual(response.status_code, 204)

        response = self.client.get(url)

        self.assertIn('UnitTest\n', str(response.data))

    def test_preview_markdown_page(self):
        # Test if we can preview a md content as HTML.
        txt = "My New Page\n========="

        data = {
            "raw_content": txt
        }
        response = self.client.post(url_for('md-render'), data=data)

        self.assertEqual(response.status_code, 200)

        self.assertIn('<h1>My New Page</h1>', str(response.data))
