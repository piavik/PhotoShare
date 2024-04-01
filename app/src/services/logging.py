from fastapi import Response, Request
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse
from fastapi.routing import APIRoute
from typing import Callable
import logging
import httpx

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)


class LoggingRoute(APIRoute):
    """
    APIRoute class replacement to enable verbose logging
    """    
    def get_route_handler(self) -> Callable:
        
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            req_body = await request.body()
            logging.info(f"{request.headers=}")
            response = await original_route_handler(request)
            tasks = response.background
            
            if isinstance(response, StreamingResponse):
                res_body = b''
                async for item in response.body_iterator:
                    res_body += item
                  
                task = BackgroundTask(log_info, req_body, res_body)
                response = Response(content=res_body, status_code=response.status_code, 
                        headers=dict(response.headers), media_type=response.media_type)
            else:
                task = BackgroundTask(log_info, req_body, response.body)
            
            # check if the original response had background tasks already attached to it
            if tasks:
                tasks.add_task(task)  # add the new task to the tasks list
                response.background = tasks
            else:
                response.background = task
                
            return response
            
        return custom_route_handler

logging.basicConfig(filename='info.log', level=logging.DEBUG)