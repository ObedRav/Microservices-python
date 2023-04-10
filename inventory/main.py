from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
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

class Product(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = redis


@app.get('/products')
def all():
    return [format(pk) for pk in Product.all_pks()]

def format(pk: str):
    product = Product.get(pk=pk)

    return {
        'id': product.pk,
        'name': product.name,
        'price': product.price,
        'quantity': product.quantity
    }

@app.post('/create')
def create(product: Product):
    return product.save()
