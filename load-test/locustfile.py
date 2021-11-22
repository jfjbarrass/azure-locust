from locust import task, between
from locust.exception import RescheduleTask
from locust_plugins.users import RestUser
from json import JSONEncoder, JSONDecoder, JSONDecodeError
from paths import Paths
import os

class TfsUser(RestUser):
    wait_time = between(3, 30)
    test_data_list = []
    access_token = ""
    identity_api = Paths.domain + Paths.identity_token
    application_request_api = Paths.finance_application_service + Paths.apply
    proposal_number = ""
    application_status_api = Paths.finance_application_service + Paths.proposal_status

    def on_start(self):
        self.get_test_data_list(self)
        self.authenticate(self)

    def get_test_data_list(self):
        self.test_data_list = os.listdir("../test-data")

    def authenticate(self):
        with self.client.post(self.identity_api, json = {}) as response:
            try:
                if response.json()["access_token"] is not None:
                    self.access_token = response.json()["access_token"]
            except JSONDecodeError:
                response.failure("response does not decode to JSON")
            except KeyError:
                response.failure("response did not return access token")

    @task
    def make_request(self):
        for x in self.test_data_list:
            try:
                user_data = self.get_test_data("../test-data/" + x)
                self.apply(self, user_data)
                if user_data["FinanceProposal"]["GetDecision"] is False:
                    self.get_proposal_status(self, self.proposal_number, user_data["Controls"])
            except JSONDecodeError:
                raise RescheduleTask()

    def get_test_data(path):
        with open(path, "r") as file:
            data = file.read()

        return JSONDecoder.loads(data)

    def apply(self, test_data):
        with self.client.post(self.application_request_api, test_data) as response:
            try:
                self.proposal_number = response.json()["applicationResponse"]["proposalNumber"]
            except JSONDecodeError:
                response.failure("response does not decode to JSON")
            except KeyError:
                response.failure("response did not return Proposal Number")

    def get_proposal_status(self, proposal_number, controls):
        with self.client.post(self.application_status_api, json = {"Controls": controls, "ProposalNumber": proposal_number}) as response:
            try:
                if response.json()["applicationResponse"]["proposalStatus"] != "PR":
                    response.failure("Did not get expected Proposal Status")
            except JSONDecodeError:
                response.failure("response does not decode to JSON")
            except KeyError:
                response.failure("response did not return Proposal Status")

