from random import Random
from locust import task, between
from locust.exception import RescheduleTask
from locust_plugins.users import RestUser
from json import JSONDecoder, JSONDecodeError
from paths import Paths
import os

class TfsUser(RestUser):
    wait_time = between(3, 30)
    user_data = {}
    access_token = ""
    identity_api = Paths.domain + Paths.identity_token
    application_request_api = Paths.finance_application_service + Paths.apply
    proposal_number = ""
    application_status_api = Paths.finance_application_service + Paths.proposal_status

    def on_start(self):
        self.get_user_data(self)
        self.authenticate(self)

    def get_user_data(self):
        test_data_list = os.listdir("./test-data")
        sample_file_path = Random.sample(test_data_list, 1)
        self.user_data = self.get_test_data(sample_file_path)

    def get_test_data(path):
        with open(path, "r") as file:
            data = file.read()

        return JSONDecoder.loads(data)

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
    def apply(self, test_data):
        with self.client.post(self.application_request_api, test_data) as response:
            try:
                self.proposal_number = response.json()["applicationResponse"]["proposalNumber"]
            except JSONDecodeError:
                response.failure("response does not decode to JSON")
            except KeyError:
                response.failure("response did not return Proposal Number")

    @task
    def get_proposal_status(self):
        if self.user_data["FinanceProposal"]["GetDecision"] is True:
            return
            
        with self.client.post(self.application_status_api, json = {"Controls": self.user_data["Controls"], "ProposalNumber": self.proposal_number}) as response:
            try:
                if response.json()["applicationResponse"]["proposalStatus"] != "PR":
                    response.failure("Did not get expected Proposal Status")
            except JSONDecodeError:
                response.failure("response does not decode to JSON")
            except KeyError:
                response.failure("response did not return Proposal Status")

