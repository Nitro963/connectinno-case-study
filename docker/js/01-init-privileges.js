db = db.getSiblingDB(process.env['MONGO_AUTH_DATABASE']);
db.createUser(
        {
            user: process.env['MONGO_TEST_USER'],
            pwd: process.env['MONGO_TEST_PASSWORD'],
            roles: [
                {
                    role: "readWrite",
                    db: process.env['MONGO_TEST_DATABASE']
                },
                {
                    role: "read",
                    db: "test"
                },
            ]
        }
);
db.createUser(
        {
            user: process.env['MONGO_USER'],
            pwd: process.env['MONGO_PASSWORD'],
            roles: [
                {
                    role: "readWrite",
                    db: process.env['MONGO_INITDB_DATABASE']
                },
                                {
                    role: "readWrite",
                    db: process.env['MONGO_TEST_DATABASE']
                },
                {
                    role: "read",
                    db: "test"
                },

            ]
        }
);
db.createUser(
        {
            user: process.env['MONGO_READONLY_USER'],
            pwd: process.env['MONGO_READONLY_PASSWORD'],
            roles: [
                {
                    role: "read",
                    db: process.env['MONGO_TEST_DATABASE']
                },
                {
                    role: "read",
                    db: process.env['MONGO_INITDB_DATABASE']
                },
                {
                    role: "read",
                    db: "test"
                },
            ]
        }
);

db = db.getSiblingDB(process.env['MONGO_INITDB_DATABASE']);
db.createCollection("test");
db = db.getSiblingDB(process.env['MONGO_TEST_DATABASE']);
db.createCollection("test");
