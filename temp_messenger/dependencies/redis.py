from redis import StrictRedis
from nameko.extensions import DependencyProvider
from uuid import uuid4

class RedisError(Exception):
    pass

class RedisClient:


    def __init__(self,url):
        self.redis = StrictRedis.from_url(
            url, decode_responses=True
        )


    def get_message(self,message_id):
        message = self.redis.get(message_id)

        if message is None:
            raise RedisError(
                'Message not found: {}'.format(message_id)
            )

        return message

    def save_message(self,email, message):
        message_id = uuid4().hex
        payload = {
            'email': email,
            'message': message
        }

        self.redis.hmset(message_id,payload)

        self.redis.pexpire(message_id,3000)
        return message_id

    def get_all_messages(self):
        return [
            {
                'id': message_id,
                'email': self.redis.hget(message_id,'email'),
                'message': self.redis.hget(message_id,'message'),
                'expires_in': self.redis.pttl(message_id)
            }
            for message_id in self.redis.keys()
        ]


class MessageStore(DependencyProvider):

    #called when Nameko service starts
    def setup(self):
        redis_url = self.container.config['REDIS_URL']
        self.client = RedisClient(redis_url)

    #called when Nameko service is shutting down
    def stop(self):
        del self.client
    #when entry point fires, Nameko creates a worker and rejects results of class for each dependency specified
    # in the service into the worker
    def get_dependency(self, worker_ctx):
        return self.client
