__author__ = 'samrichards'

    # TODO cut out for URLs / routing tests
    # def test_auth(self):
    #     """
    #     Test unauthorized api access
    #     """
    #     self.client.logout()
    #     response = self.client.get(self.BASE_URL)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # TODO Move to a URL routing test
    # def test_get_base(self):
    #     """
    #     get on the base url.
    #     """
    #     response1 = self.client.get(self.BASE_URL)
    #     self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)

        # TODO test get nonexistant item for each
        # e_msg = ('Not found')
        # response3 = self.client.get('%s/raid0pool' % self.BASE_URL)
        # self.assertEqual(response3.status_code,
        #                  status.HTTP_404_NOT_FOUND, msg=response3.data)
        # self.assertEqual(response3.data['detail'], e_msg)