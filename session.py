import aiohttp
import asyncio #testing purpouses
from settings import API_AUTH
import json
import logging

class WebSession(object):
    session = None

    @classmethod
    def create(cls):
        cls.session = aiohttp.ClientSession()
        #print(f'{cls.session} created')
        return cls.session

    @classmethod
    def close(cls):
        if cls.session is not None:
            # apparently this is supposed to return a future?
            return cls.session.close()


async def request(method, url,raw=False, **kwargs):

    if WebSession.session is None:
        session = WebSession.create()
    else:
        session = WebSession.session

    if(method=='GET'):
        response = await session.get(url=url, **kwargs)
        if not raw:
            response = await response.text()
            response = json.loads(response)
            return response
            # try:
            #     response = json.loads(response)
            # except json.decoder.JSONDecodeError:
            #     logging.error(f"[JSON DECODE ERROR] {response}")
            #     #raise json.decoder.JSONDecodeError
            #     return 0 
            # except Exception as e:
            #     logging.error(f"[{e}] {response}")
            #     return 0
        return response
    elif(method=='POST'):
        return await session.post(url=url, **kwargs)
    else:
        return await session.request(method=method, url=url, **kwargs)

async def get(url, **kwargs):
    return await request('GET', url=url, **kwargs)


async def post(url, **kwargs):
    return await request('POST', url=url, **kwargs)


# run this before the app ends
async def close():
    await WebSession.close()


if __name__ =='__main__':
    pass