#!/usr/bin/python3
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
import requests, time, uvicorn
from os import getenv

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[getenv('FRONTED_URL')],
    allow_methods=['*'],
    allow_headers=['*']
)

redis = get_redis_connection(
    host=getenv('REDIS_HOST'),
    port=getenv('REDIS_PORT'),
    password=getenv('REDIS_PASSWD'),
    decode_responses=True
)

class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str # pending, completed, refunded

    class Meta:
        database = redis

@app.get('/orders')
def all():
    return [format(pk) for pk in Order.all_pks()]

def format(pk: str):
    order = Order.get(pk=pk)

    return {
        'id': order.pk,
        'product_id': order.product_id,
        'price': order.price,
        'fee': order.fee,
        'total': order.total,
        'quantity': order.quantity,
        'status': order.status
    }

@app.get('/orders/{id}')
def get_orders(id: str):
    return Order.get(id)


@app.post('/orders')
async def create_order(request: Request, background_task: BackgroundTasks):
    body = await request.json()

    req = requests.get(f"{getenv('URL_INVENTORY_MICROSERVICE')}/products/{body.get('id')}")
    product = req.json()

    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending'
    )

    order.save()

    background_task.add_task(order_completed, order)

    return order


def order_completed(order: Order):
    time.sleep(5) # Payment response timeout
    order.status = 'completed'
    order.save()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
