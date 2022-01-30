INSERT INTO companys (name, owner)
VALUES
    ('test', 'Angel');

INSERT INTO users (c_id, username, email, hash, role)
VALUES
    (1, 'Angel', 'angellopez20@gmail.com', 'pbkdf2:sha256:150000$si0i9DXt$d740b53f1e6493668d9fc8b2adc3e4c8f0c983a87153c9e8fa8024e6fe731e40', 'owner'),
    (1, 'Rossana', 'rossana.sanchez@gmail.com', 'pbkdf2:sha256:150000$Qg4s6K0Q$8ab66a9b1db837a43b15908fa4b68aad3fa1217fa9f8319620e16a4e3a91bd05', 'user'),
    (1, 'test', 'test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 'admin'),
    (1, 'test2', 'test2', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 'user');

INSERT INTO vehicles (c_id, make, model, year, number, vin, tag)
VALUES
    (1, 'FORD', 'F-550', 2018, '8', 'whatever', NULL),
    (1, 'BMW', 'X-3', 2020, '2', 'bmwvin', NULL),
    (1, 'TOYOTA', 'Camry', 2014, '4', 'toyotavin', NULL),
    (1, 'CHEVROLET', 'Traverse', 2011, '1', 'anothervin', NULL);

INSERT INTO inspections (c_id, u_id, v_id, miles, next_oil, date, leak_sign, leak_sign_t, doors_open, doors_open_t)
VALUES
    (1, 1, 1, 3000, 7000, '2022-01-03', 0, 'Looks like there is a leak', 1, NULL),
    (1, 2, 2, 10000, 12000, '2022-01-03', 1, NULL, 1, NULL),
    (1, 1, 3, 100, 3500, '2022-01-03', 1, NULL, 1, NULL),
    (1, 1, 1, 3700, 7000, '2022-01-10', 0, 'Leak continues', 1, NULL),
    (1, 2, 2, 11200, 12000, '2022-01-10', 1, NULL, 1, NULL),
    (1, 1, 1, 4100, 7000, '2022-01-17', 1, NULL, 0, 'A weird sound when opening, maybe is the rain?'),
    (1, 2, 2, 12100, 12000, '2022-01-17', 1, NULL, 1, NULL);