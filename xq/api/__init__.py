import requests

from xq.config import API_KEY, DASHBOARD_API_KEY, XQ_LOCATOR_KEY, API_BASE_URI
from xq.exceptions import SDKConfigurationException


class XQAPI:

    # import submodules as methods
    from xq.api.subscription import (
        validate_api_key,
        authorize_user,
        code_validate,
        exchange_key,
        create_packet,
        create_and_store_packet,
        create_and_store_packets,
        authorize_alias,
        authorize_device
    )
    from xq.api.validation import (
        get_packet,
        get_packets,
        add_packet,
        revoke_packet,
        grant_users,
        revoke_users,
    )
    from xq.api.quantum import get_entropy
    from xq.api.manage import (
        dashboard_signup,
        dashboard_login,
        create_usergroup,
        get_usergroup,
        update_usergroup,
        delete_usergroup,
        add_contact,
        send_login_link,
        validate_access_token,
        login_verify,
        get_communication_by_locator_token,
        announce_device
    )

    def __init__(
        self,
        api_key=API_KEY,
        dashboard_api_key=DASHBOARD_API_KEY,
        locator_key=XQ_LOCATOR_KEY,
        api_base_uri=API_BASE_URI,
    ):

        self.api_key = api_key
        self.dashboard_api_key = dashboard_api_key
        self.locator_key = locator_key
        self.api_base_uri = api_base_uri
        self.session = requests.Session()
        self.headers = {
            "authorization": "Bearer xyz123",
            "Content-Type": "application/json",
        }

        if not (self.api_key and self.dashboard_api_key):
            raise SDKConfigurationException
        else:
            self.headers["api-key"] = self.api_key
            self.validate_api_key()

    def api_get(self, serviceEndpoint, subdomain, params={}):
        """static method for interacting with the XQ API GET endpoints

        :param serviceEndpoint: uri service extension to hit
        :type serviceEndpoint: string
        :param subdomain: subdomain of uri to use, api specific
        :type subdomain: string
        :param params: optional parameters to pass, defaults to {}
        :type params: dict
        :param headers: optional headers to pass, defaults to {}
        :type headers: dict
        :return: requests obj
        :rtype: requests response
        """
        r = self.session.get(
            f"https://{subdomain}.{self.api_base_uri}{serviceEndpoint}",
            params=params,
            headers=self.headers,
        )

        try:
            res = r.json()
        except Exception as e:
            res = r.text

        return r.status_code, res

    def api_post(self, serviceEndpoint, subdomain, json=None, data=None):
        """static method for interacting with XQ API POST endpoints

        :param serviceEndpoint: uri service extension to hit
        :type serviceEndpoint: string
        :param subdomain: subdomain of uri to use, api specific
        :type subdomain: string
        :param json: optional parameters to pass, POSTS as json contenttype, defaults to None
        :type json: dict, optional
        :param data: optional parameters to pass, defaults to None
        :type data: dict, optional
        :return: status code, response
        :rtype: tuple(int, string)
        """
        r = self.session.post(
            f"https://{subdomain}.{self.api_base_uri}{serviceEndpoint}",
            json=json,
            data=data,
            headers=self.headers,
            timeout=30,
        )

        try:
            res = r.json()
        except Exception as e:
            res = r.text

        return r.status_code, res

    def api_put(self, serviceEndpoint, subdomain, json=None, data=None):
        """static method for interacting with XQ API PUT endpoints

        :param serviceEndpoint: uri service extension to hit
        :type serviceEndpoint: string
        :param subdomain: subdomain of uri to use, api specific
        :type subdomain: string
        :param json: optional parameters to pass, POSTS as json contenttype, defaults to None
        :type json: dict, optional
        :param data: optional parameters to pass, defaults to None
        :type data: dict, optional
        :return: status code, response
        :rtype: tuple(int, string)
        """
        r = self.session.put(
            f"https://{subdomain}.{self.api_base_uri}{serviceEndpoint}",
            json=json,
            data=data,
            headers=self.headers,
        )

        try:
            res = r.json()
        except Exception as e:
            res = r.text

        return r.status_code, res

    def api_delete(self, serviceEndpoint, subdomain):
        """static method for interacting with XQ API DELETE endpoints

        :param serviceEndpoint: uri service extension to hit
        :type serviceEndpoint: string
        :param subdomain: subdomain of uri to use, api specific
        :type subdomain: string
        :return: status code, response
        :rtype: tuple(int, string)
        """
        r = self.session.delete(
            f"https://{subdomain}.{self.api_base_uri}{serviceEndpoint}",
            headers=self.headers,
        )

        try:
            res = r.json()
        except Exception as e:
            res = r.text

        return r.status_code, res

    def api_patch(self, serviceEndpoint, subdomain, data=None, json=None):
        """static method for interacting with XQ API PATCH endpoints

        :param serviceEndpoint: uri service extension to hit
        :type serviceEndpoint: string
        :param subdomain: subdomain of uri to use, api specific
        :type subdomain: string
        :param data: optional parameters to pass, defaults to None
        :type data: dict, optional
        :param json: optional parameters to pass, POSTS as json contenttype, defaults to None
        :type json: dict, optional
        :return: status code, response
        :rtype: tuple(int, string)
        """
        r = self.session.patch(
            f"https://{subdomain}.{self.api_base_uri}{serviceEndpoint}",
            data=data,
            json=json,
            headers=self.headers,
        )

        try:
            res = r.json()
        except Exception as e:
            res = r.text

        return r.status_code, res
