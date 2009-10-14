# coding: utf-8

from django.test import Client, TestCase
from polls.models import Poll

from django.test.client import urlparse, urllib, settings, FakePayload, \
    encode_multipart, MULTIPART_CONTENT, CONTENT_TYPE_RE, BOUNDARY
def put(self, path, data={}, content_type=MULTIPART_CONTENT,
         follow=False, **extra):
    """
    Requests a response from the server using POST.
    """
    if content_type is MULTIPART_CONTENT:
        post_data = encode_multipart(BOUNDARY, data)
    else:
        # Encode the content so that the byte representation is correct.
        match = CONTENT_TYPE_RE.match(content_type)
        if match:
            charset = match.group(1)
        else:
            charset = settings.DEFAULT_CHARSET
        post_data = smart_str(data, encoding=charset)

    parsed = urlparse(path)
    r = {
        'CONTENT_LENGTH': len(post_data),
        'CONTENT_TYPE':   content_type,
        'PATH_INFO':      urllib.unquote(parsed[2]),
        'QUERY_STRING':   parsed[4],
        'REQUEST_METHOD': 'PUT',
        'wsgi.input':     FakePayload(post_data),
    }
    r.update(extra)

    response = self.request(**r)
    if follow:
        response = self._handle_redirects(response)
    return response

# Patch the test Client so that PUT data is put in the proper location.
Client.put = put

class PollResourceTest(TestCase):
    fixtures = ['testdata']

    def test_meta_handler(self):
        count = Poll.objects.count()
        response = self.client.get('/api/models/polls/poll/meta/')
        self.assertEqual(response.status_code, 200)

    def test_length_view(self):
        count = Poll.objects.count()
        response = self.client.get('/api/models/polls/poll/length/')
        self.assertContains(response, count)

    def test_list_view(self):
        response = self.client.get('/api/models/polls/poll/list/')
        self.assertContains(response, 'What color are your socks?')

    def test_show_view(self):
        response = self.client.get('/api/models/polls/poll/?pk=1')
        self.assertContains(response, 'What color are your socks?')
        self.assertContains(response, '1')

    def test_create_post(self):
        poll_data = {
            "question": "What is your favorite color?",
            "slug": "favorite-color",
        }
        response = self.client.post('/api/models/polls/poll/', poll_data)
        self.assertContains(response, 'What is your favorite color?')
        self.assertNotContains(response, '1')

    def test_create_json(self):
        json_data = """
        {
            "question": "What is your favorite color?",
            "slug": "favorite-color"
        }
        """

        response = self.client.post('/api/models/polls/poll/', json_data,
                                    content_type='application/json')
        self.assertContains(response, 'What is your favorite color?', status_code=200)

    def test_update_post(self):
        poll_data = {
            "question": "What is your favorite color?",
            "slug": "favorite-color",
        }
        response = self.client.put('/api/models/polls/poll/?pk=1', poll_data)
        self.assertContains(response, 'What is your favorite color?')
        self.assertContains(response, '1')

    def test_destroy(self):
        count = Poll.objects.count()
        response = self.client.delete('/api/models/polls/poll/?pk=1')
        self.assertEqual(response.content, '')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Poll.objects.count(), count - 1)
