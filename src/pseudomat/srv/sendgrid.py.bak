import base64
from collections import deque
import hashlib
import logging
from time import time
import typing as T

from aiohttp import web
import aiohttp
from sendgrid.helpers.mail import Mail

from pseudomat.common import json_dumps

_logger = logging.getLogger(__package__)
_html_content = """<html><head></head><body><p>Dear project owner,</p>

<p>&nbsp;</p>

<p>You, or someone pretending to be you, has just created a Pseudomat project<br/>
named <b>{name}</b>.</p>

<p>Before you can start using this project, you must confirm its email address<br/>
<tt>{email}</tt> with the following code:</p>

<p><b><tt>{code}</tt></b></p>

<p>You can do this by running the following command on your computer:</p>

<p><tt><b>pseudomat project verify {code}</b></tt></p>

<p>If the project is not your current default project, you’ll have to specify the<br/>
project ID too:</p>

<p><tt><b>pseudomat project verify --project-id {project_id} {code}</b></tt></p>

<p>&nbsp;</p>

<p>Kind regards,<br/>
The Pseudomat Team</p></body></html>"""
_client_timeout = aiohttp.ClientTimeout(
    total=10
)
_send_timestamps: T.Dict[str, T.Deque[float]] = {}


def context(app: aiohttp.web.Application) -> T.AsyncContextManager:
    return aiohttp.ClientSession(
        json_serialize=json_dumps,
        timeout=_client_timeout,
        headers={'Authorization': "Bearer %s" % app['config']['sendgrid']['api_key']},
    )


async def send_confirmation_mail(
    app: web.Application,
    email: str,
    name: str,
    project_id: str
):
    # Rate limiting:
    if email not in _send_timestamps:
        _send_timestamps[email] = deque()
    timestamps = _send_timestamps[email]
    yesterday = time() - 24 * 60 * 60
    while len(timestamps) and timestamps[0] < yesterday:
        timestamps.popleft()
    timestamps.append(time())
    if len(timestamps) > 10:
        raise web.HTTPTooManyRequests(
            text="You can create at most 10 projects per email address per day."
        )

    code = base64.urlsafe_b64encode(
        hashlib.sha256(
            json_dumps([
                project_id, app['config']['pseudomat']['secret']
            ]).encode('utf-8')
        ).digest()[:24]
    ).decode('utf-8')
    mail_vars = {
        'name': name,
        'email': email,
        'project_id': project_id,
        'code': code
    }
    m = Mail(
        from_email='p.van.beek@amsterdam.nl',
        to_emails=email,
        subject="Pseudomat email address confirmation",
        html_content=_html_content.format(**mail_vars)
    )

    try:
        async with app['sgsession'].post(
                app['config']['sendgrid']['url'],
                json=dict(m.get())
        ) as response:
            assert response.status in range(200, 300), \
                "Couldn’t send mail. Sendgrid returned HTTP status %d\n%s" % (
                    response.status, await response.text()
                )
    except (aiohttp.ClientError, AssertionError) as e:
        _logger.exception(e)
        raise web.HTTPBadGateway(
            text="Couldn’t send confirmation email."
        )
