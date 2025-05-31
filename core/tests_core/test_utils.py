from django.test import TestCase
from core.utils import remove_quoted_text

class TestRemoveQuotedText(TestCase):
    def test_gmail_quote_pattern(self):
        body = """Hello,

This is my response.

On Mon, May 20, 2024 at 10:00 AM, John Doe <john@example.com> wrote:
> Previous message content
> More quoted content"""
        
        expected = "Hello,\n\nThis is my response."
        self.assertEqual(remove_quoted_text(body), expected)

    def test_outlook_quote_pattern(self):
        body = """Hi there,

Here's my reply.

-----Original Message-----
From: Jane Smith <jane@example.com>
Sent: Monday, May 19, 2024 3:45 PM
To: John Doe <john@example.com>
Subject: RE: Meeting

Previous message content"""
        
        expected = "Hi there,\n\nHere's my reply."
        self.assertEqual(remove_quoted_text(body), expected)

    def test_common_quote_marker(self):
        body = """Thanks for your email.

> This is quoted text
> More quoted text"""
        
        expected = "Thanks for your email."
        self.assertEqual(remove_quoted_text(body), expected)

    def test_outlook_header_pattern(self):
        body = """Please find my response below.

From: Timothée Soissons <timothee.soissons@mplus.software>
Sent: Tuesday, May 20, 2025 12:08:29 PM
To: Sam Ng <samng@scorptec.com.au>
Cc: Raphael Alla <raphael.alla@mplus.software>; Tam Nguyen <tam@mplus.software>
Subject: Odoo implementation proposal of Purchase for Scorptec - S04408

Previous message content"""
        
        expected = "Please find my response below."
        self.assertEqual(remove_quoted_text(body), expected)

    def test_multiple_quote_patterns(self):
        body = """My response.

On Mon, May 20, 2024 at 10:00 AM, John Doe <john@example.com> wrote:
> Previous message
> 
> -----Original Message-----
> From: Jane Smith <jane@example.com>
> Sent: Monday, May 19, 2024 3:45 PM
> To: John Doe <john@example.com>
> Subject: RE: Meeting
> 
> Original message content"""
        
        expected = "My response."
        self.assertEqual(remove_quoted_text(body), expected)

    def test_no_quotes(self):
        body = """This is a simple message
with no quoted content."""
        
        self.assertEqual(remove_quoted_text(body), body)

    def test_empty_body(self):
        self.assertEqual(remove_quoted_text(""), "") 