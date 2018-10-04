from uuid import UUID, uuid4

from serde import Array, Boolean, Field, Float, Integer, Map, Model, Parts, String


def test_base_0():

    class Uuid(Field):

        def serialize(self, value):
            return str(value)

        def deserialize(self, value):
            return UUID(value)

        def validate(self, value):
            assert isinstance(value, UUID)

    class Player(Model):
        key = Uuid(optional=True)
        name = Parts(String, String)
        age = Integer()
        rating = Float()

    class Game(Model):
        finished = Boolean()
        players = Array(Player)
        board = Map(String, Integer)

    # Create a player manually
    random_uuid = uuid4()
    player = Player(('James', 'Williams'), 23, 52.3, key=random_uuid)

    assert player.key == random_uuid
    assert player.name == ('James', 'Williams')
    assert player.age == 23
    assert player.rating == 52.3

    # Deserialize a Game from JSON
    json = """{
    "board": {
        "BC": 0,
        "BL": 0,
        "BR": 0,
        "CC": 1,
        "CL": 0,
        "CR": 0,
        "TC": 0,
        "TL": -1,
        "TR": 0
    },
    "finished": false,
    "players": [
        {
            "age": 51,
            "key": "5a47a83b-72d3-4231-b8f6-3c21b635782c",
            "name": [
                "John",
                "Smith"
            ],
            "rating": 65.2
        },
        {
            "age": 43,
            "key": "4f24e615-f4dd-4e69-b2dc-76392e2b1763",
            "name": [
                "Mary",
                "Jones"
            ],
            "rating": 71.0
        }
    ]
}"""

    game = Game.from_json(json)

    assert game.finished is False

    assert game.players[0].key == UUID('5a47a83b-72d3-4231-b8f6-3c21b635782c')
    assert game.players[0].name == ('John', 'Smith')
    assert game.players[0].age == 51
    assert game.players[0].rating == 65.2

    assert game.players[1].key == UUID('4f24e615-f4dd-4e69-b2dc-76392e2b1763')
    assert game.players[1].name == ('Mary', 'Jones')
    assert game.players[1].age == 43
    assert game.players[1].rating == 71.0

    assert game.board == {'TL': -1, 'TC': 0, 'TR': 0,
                          'CL': 0, 'CC': 1, 'CR': 0,
                          'BL': 0, 'BC': 0, 'BR': 0}

    assert game.to_json(indent=4, sort_keys=True) == json


def test_base_1():
    class Address(Model):
        email = String()

    class User(Model):
        name = String(rename='username')
        age = Integer(optional=True)
        addresses = Array(Address, optional=True)

    # Serialization
    user = User('John Smith', age=53, addresses=[Address('john@smith.com')])
    assert user.to_dict() == {'username': 'John Smith',
                              'age': 53,
                              'addresses': [{'email': 'john@smith.com'}]}

    # Deserialization
    user = User.from_dict({'username': 'John Smith',
                           'age': 53,
                           'addresses': [{'email': 'john@smith.com'}]})
    assert user.name == 'John Smith'
    assert user.age == 53
    assert user.addresses == [Address('john@smith.com')]
