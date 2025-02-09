from aioclock import Group, AioClock, Forever

            email_group = Group()

            # consider this as different file
            @email_group.task(trigger=Forever())
            async def send_email():
                ...

            # app.py
            aio_clock = AioClock()
            aio_clock.include_group(email_group)
from aioclock import Group, Forever
            @group.task(trigger=Forever())
            async def send_email():
                ...