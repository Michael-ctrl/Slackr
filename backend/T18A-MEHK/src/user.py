'''
Allows users to edit and set their profile information
'''
import requests
from PIL import Image
from src.utils import check_token, generate_random_string, get_user_information
from src.auth_helper import is_handle_unique, is_email_valid, id_from_email, is_name_valid
from src.error import InputError
from src.global_variables import get_users
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def is_valid_handle(host_user_id, handle_str):
    '''Checks that handle_str is valid and not being used by any other user

    :param host_user_id: Id of the user changing their handle
    :type host_user_id: int
    :param handle_str: User's new handle
    :type handle_str: str
    :return: True if the new handle_str is the same as the old, or if it is both valid AND unique.
    :rtype: bool
    '''
    users = get_users()
    if users[host_user_id]['handle_str'] == handle_str:
        return True
    return is_handle_unique(handle_str) and len(handle_str) >= 2 and len(handle_str) <= 20

def is_new_email(host_user_id, email):
    '''Checks that email is valid and not being used by any other user

    :param host_user_id: Id of the user changing their email
    :type host_user_id: int
    :param email: User's new email
    :type email: str
    :return: True if the new email is the same as the old, or if the email is both valid AND unique.
    :return: False, Otherwise
    :rtype: bool
    '''
    email_id = id_from_email(email)
    return email_id == host_user_id or (is_email_valid(email) and email_id is None)

def user_profile(token, user_id):
    '''finds and returns a user profile

    :param token: jwt token
    :type token: str
    :param user_id: id corresponding to the target user
    :type user_id: int
    :return: contains u_id, email, name_first, name_last, handle_str
    :rtype: dict
    '''
    check_token(token)
    return {'user': get_user_information(user_id)}


def user_profile_setname(token, name_first, name_last):
    '''Given a valid token, name_first, name_last, updates a users name_first, name_last

    :param token: jwt token
    :type token: str
    :param name_first: new first name
    :type name_first: str
    :param name_last: new last name
    :type name_last: str
    :raises InputError: if either name_first or name_last is invalid
    :return: empty dictionary
    :rtype: dict
    '''
    user_id = check_token(token)
    if not (is_name_valid(name_first) and is_name_valid(name_last)):
        raise InputError(description='Names must be between 1 and 50 characters')

    user = get_users()[user_id]
    user['name_first'] = name_first
    user['name_last'] = name_last

    return {}


def user_profile_setemail(token, email):
    '''Given a valid token and new email, updates a user's email address

    :param token: jwt token
    :type token: str
    :param email: new email
    :type email: str
    :raises InputError: If email is invalid according to is_new_email()
    :return: empty dictionary
    :rtype: dict
    '''
    user_id = check_token(token)
    if not is_new_email(user_id, email):
        raise InputError(description='Email invalid or already being used')

    user = get_users()[user_id]
    user['email'] = email
    return {}


def user_profile_sethandle(token, handle_str):
    '''Given a valid new handle_str and token, updates a user's handle_str

    :param token: jwt token
    :type token: str
    :param handle_str: new handle
    :type handle_str: str
    :raises InputError: If handle_str is invalid according to is_valid_handle()
    :return: empty dictionary
    :rtype: dict
    '''
    user_id = check_token(token)
    if not is_valid_handle(user_id, handle_str):
        raise InputError(description='Handle invalid or already being used')

    user = get_users()[user_id]
    user['handle_str'] = handle_str
    return {}


def user_profile_setimage(token, img_url, x_start, y_start, x_end, y_end): #pylint: disable=too-many-arguments
    '''
    Update the authorised user's display photo
    Downloads the given img_url into the server folder 'images'
    Crops images if they do not fit the size
    :param token:
    :type token: string
    '''
    user_id = check_token(token)
    user = get_users()[user_id]

    file_extension = img_url.rsplit('.', 1)[1].lower()
    if not file_extension in ALLOWED_EXTENSIONS:
        raise InputError(description="file not allowed")

    if not x_start < x_end:
        raise InputError(description="x_start must be larger than x_end")
    if not y_start < y_end:
        raise InputError(description="y_start must be larger than y_end")

    try:
        image = requests.get(img_url, allow_redirects=True).content
    except:
        raise InputError(description="could not download image")

    new_file_name = f'{generate_random_string(20)}.{file_extension}'
    new_image = open(f'images/original/{new_file_name}', 'wb')
    new_image.write(image)

    original_image = Image.open(f'images/original/{new_file_name}')
    original_image = original_image.crop((x_start, y_start, x_end, y_end))
    cropped_image = open(f'images/cropped/{new_file_name}', 'wb')
    original_image.save(cropped_image)

    user['profile_img_url'] = f'/imgurl/{new_file_name}'
    return {}
