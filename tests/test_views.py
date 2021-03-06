import pytest

def test_index(client):
    assert client.get("/").status_code == 200

home = "http://localhost/"
content = "http://localhost/content"

def _unlock_db(cli):
    # set master password, or unlock. and generate a master_key object
    resp = cli.post(
        "/login",
        data={"master_pw": "test123"}
    )
    assert resp.headers["Location"] == content

@pytest.mark.parametrize("pw_sample,expected", [
    ("wrong*password", home),
    ("test123", content)    
])
def test_login(client, pw_sample, expected):
    assert client.get("/login").status_code == 405
    # database initialized and empty, attempts to create new master password
    _unlock_db(client)
    
    resp = client.get("/lock")
    assert resp.headers["Location"] == home
    resp = client.post(
        "/login",
        data={"master_pw": pw_sample}
    )
    assert resp.headers["Location"] == expected

@pytest.mark.parametrize("pw_sample,expected", [
    ("wrong*password", home),
    ("test123", home),
    ("test_new_pw", content)
])
def test_change_masterpw(client, pw_sample, expected):
    assert client.get("/change_pw").status_code == 405
    _unlock_db(client)
    resp = client.post(
        "/change_pw",
        data={"master_pw": "test_new_pw"}
    )
    assert resp.headers["Location"] == content
    resp = client.get("/lock")
    assert resp.headers["Location"] == home
    resp = client.post(
        "/login",
        data={"master_pw": pw_sample}
    )
    assert resp.headers["Location"] == expected

def test_content(client):
    _unlock_db(client)
    assert client.get("/content").status_code == 200

@pytest.mark.parametrize("url_sample,expected", [
    ("", content),
    (" ", content),
    ("abc.com", "http://localhost/add/abc.com"),
    ("abc.com/login/user", "http://localhost/add/abc.com"),
    ("something.io", "http://localhost/add/something.io"),
    ("thisthat.xyz", "http://localhost/add/thisthat.xyz")
])
def test_search(client, url_sample, expected):
    resp = client.post(
        "/search",
        data={"url_read": url_sample}
    )
    assert resp.headers["Location"] == expected
    
    _unlock_db(client)
    resp = client.post(
        "/insert_db/sillydomainname.com",
        data={
            "url_read": "sillydomainname.com",
            "password": ""}
    )
    assert resp.headers["Location"] == content + "/1001"
    resp = client.post(
        "/search",
        data={"url_read": "sillydomainname.com"}
    )
    assert resp.headers["Location"] == content + "/1001"
    resp = client.get("/content/1001")
    assert resp.status_code == 200
    result_pw = resp.data.split(b"""id="btn-copyPass" value=""")[1].split(b""">Copy Password""")[0]

    resp = client.post(
        "/generate_new",
        data={"generate_new": 1001}
    )
    result_pw_new = resp.data.split(b"""id="btn-copyPass" value=""")[1].split(b""">Copy Password""")[0]
    assert result_pw != result_pw_new

    resp = client.get("/update/1001")
    assert resp.status_code == 200

    resp = client.post(
        "/update_db/1001",
        data={
            "login": "new@email.com",
            "password": "",
        }
    )
    assert resp.headers["Location"] == content + "/1001"
    resp = client.get("/content/1001")
    assert b'new@email.com' in resp.data