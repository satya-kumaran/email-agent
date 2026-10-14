import base64
import unittest
from types import SimpleNamespace as NS
from agent import Mailbox, body_text, validate_report, run_agent

EMAIL = {'id': 'a', 'body': 'Please sign the form by Friday.'}
TASK = {'email_id': 'a', 'title': 'Sign form', 'evidence': 'Please sign the form by Friday.', 'deadline_text': 'by Friday'}

class FakeResponses:
    def __init__(self, calls): self.calls = iter(calls)
    def create(self, **kwargs):
        name, arguments = next(self.calls)
        import json
        return NS(output=[NS(type='function_call', name=name, arguments=json.dumps(arguments), call_id='c')], usage=None)

class AgentTests(unittest.TestCase):
    def test_reject_unread_and_fabricated_evidence(self):
        box = Mailbox([EMAIL])
        with self.assertRaises(ValueError): validate_report(box, [TASK])
        box.read_email('a')
        with self.assertRaises(ValueError): validate_report(box, [{**TASK, 'evidence': 'Pay me'}])
        with self.assertRaises(ValueError): validate_report(box, [{**TASK, 'deadline_text': 'Monday'}])
        self.assertEqual(validate_report(box, [TASK, TASK]), [TASK])
    def test_id_boundary(self):
        with self.assertRaises(ValueError): Mailbox([EMAIL]).read_email('other')
    def test_loop_corrects_premature_submission(self):
        client = NS(responses=FakeResponses([('submit_report', {'tasks': [TASK]}),
            ('read_email', {'email_id': 'a'}), ('submit_report', {'tasks': [TASK]})]))
        report = run_agent(Mailbox([EMAIL]), client, 'fake')
        self.assertEqual(report['tasks'], [TASK]); self.assertEqual(report['steps'], 3)
    def test_step_limit(self):
        client = NS(responses=FakeResponses([('read_email', {'email_id': 'a'})]))
        with self.assertRaises(RuntimeError): run_agent(Mailbox([EMAIL]), client, 'fake', max_steps=1)
    def test_plain_preferred_html_and_attachments(self):
        enc = lambda x: base64.urlsafe_b64encode(x.encode()).decode().rstrip('=')
        payload = {'parts': [{'mimeType':'text/html', 'body':{'data':enc('<p>HTML</p>')}},
                    {'mimeType':'text/plain', 'body':{'data':enc('Plain')}},
                    {'mimeType':'text/plain', 'filename':'secret.txt', 'body':{'data':enc('Attachment')}}]}
        self.assertEqual(body_text(payload), 'Plain')
        self.assertEqual(body_text({'mimeType':'text/html','body':{'data':enc('<script>bad</script><p>Hello</p>')}}).strip(), 'Hello')
    def test_truncation_and_empty(self):
        box = Mailbox([{'id':'long', 'body':'x'*24001}])
        self.assertTrue(box.read_email('long')['truncated'])
        self.assertEqual(run_agent(Mailbox([]), None, 'fake')['tasks'], [])

if __name__ == '__main__': unittest.main()
