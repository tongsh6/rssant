import logging

import backdoor
from validr import T
from actorlib import actor, collect_actors, ActorNode, ActorContext


LOG = logging.getLogger(__name__)


@actor('actor.init')
def do_init(ctx: ActorContext):
    ctx.tell('registery.register', dict(node=ctx.registery.current_node.to_spec()))


@actor('worker.ping')
def do_ping(ctx: ActorContext, message: T.str) -> T.dict(message=T.str):
    LOG.info(ctx.message)
    r = ctx.ask('registery.query')
    LOG.info(r)
    ctx.tell('worker.pong', dict(message=message))
    if message == 'error':
        raise ValueError(message)
    return dict(message=message)


@actor('worker.pong')
async def do_pong(ctx: ActorContext, message: T.str) -> T.dict(message=T.str):
    LOG.info(ctx.message)
    r = await ctx.ask('registery.query')
    LOG.info(r)
    if message == 'error':
        raise ValueError(message)
    return dict(message=message)


ACTORS = collect_actors(__name__)


def main():
    backdoor.setup()
    app = ActorNode(
        actors=ACTORS,
        port=8082,
        subpath='/api/v1/worker',
        storage_dir_path='data/actorlib_example_worker',
        storage_wal_limit=3,
        storage_compact_interval=10,
        registery_node_spec={
            'name': 'registery',
            'modules': ['registery'],
            'networks': [{
                'name': 'localhost',
                'url': 'http://127.0.0.1:8081/api/v1/registery',
            }],
        },
    )
    app.run()


if __name__ == "__main__":
    from rssant_common.logger import configure_logging
    from actorlib.sentry import sentry_init
    configure_logging()
    sentry_init()
    main()
