External API of the aioclock package, that can be used to interact with the AioClock instance.
This module could be very useful if you intend to use aioclock in a web application or a CLI tool.

Other tools and extension are written from this tool.

!!! danger "Note when writing to aioclock API and changing its state."\n    Right now the state of AioClock instance is on the memory level, so if you write an API and change a task's trigger time, it will not persist.\n    In future we might store the state of AioClock instance in a database, so that it always remains same.\n    But this is a bit tricky and implicit because then your code gets ignored and database is preferred over the database.\n    For now you may consider it as a way to change something without redeploying the application, but it is not very recommended to write.