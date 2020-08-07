#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import json
import os

from datetime import datetime
from dateutil import tz

import praw
import tweepy

import constants


class DataCollector(object):
    def __init__(self, social):
        self.social = social

        if self.social == constants.REDDIT_NAME:
            columns = constants.REDDIT_COLUMNS
            self.call_param = constants.REDDIT_START_PARAM
        elif self.social == constants.TWITTER_NAME:
            columns = constants.TWITTER_COLUMNS
            self.start_param = constants.TWITTER_START_PARAM
        else:
            raise ValueError('The class DataCollector cannot be instantiated with the given argument')

        self.df = pd.DataFrame(columns=columns)
        self.api = self.authentication()

# AUTHENTICATION

    def authentication(self):
        credentials = self.get_credentials()
        api = self.api_auth(credentials)
        return api

    def get_credentials(self):

        if not os.path.exists(constants.CREDENTIALS_FOLDER_NAME):
            os.mkdir(constants.CREDENTIALS_FOLDER_NAME)

        file_credentials = f"{constants.CREDENTIALS_FOLDER_NAME}/{self.social}_credentials.json"

        try:
            with open(file_credentials) as f:
                return json.load(f)
        except IOError:
            raise IOError('Missing files: The files with the credentials for the API cannot be found')

    def api_auth(self, credentials):
        if self.social == constants.REDDIT_NAME:
            return self.reddit_api_auth(credentials)
        elif self.social == constants.TWITTER_NAME:
            return self.twitter_api_auth(credentials)

    @staticmethod
    def reddit_api_auth(credentials):
        reddit_api = praw.Reddit(client_id=credentials['client_id'],
                                 client_secret=credentials['client_secret'],
                                 user_agent=credentials['user_agent'])
        return reddit_api

    @staticmethod
    def twitter_api_auth(credentials):
        auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
        auth.set_access_token(credentials['access_token'], credentials['access_secret'])
        twitter_api = tweepy.API(auth)
        return twitter_api

# DATA COLLECTION

    def collect_data_today(self):
        list_of_users = self.get_list_users()['user_to_follow']

        for user in list_of_users:
            results_for_user_today = self.get_today_result(user)
            self.format_and_append(results_for_user_today)
        print(self.df)

    def get_list_users(self):
        list_users = f"users/{self.social}_users.json"

        try:
            with open(list_users) as f:
                return json.load(f)
        except IOError:
            raise IOError('Missing files: The files with the users to follow cannot be found')

    # GET TODAY DATA

    def get_today_result(self, user):

        try:
            result_from_api = self.api_call(user)
        except Exception as e:
            print(e)
            return None

        if self.need_more_data(result_from_api):
            self.update_params()
            self.get_today_result(user)
        else:
            # The filter could be avoided with a remove duplicates
            # after the concat with past data
            return self.filter_extra_data(result_from_api)

    def need_more_data(self, results):
        for r in results:
            if self.past_data(r):
                return False
        return True

    def update_params(self):
        self.call_param *= 2

    def filter_extra_data(self, results):
        return [r for r in results if not self.past_data(r)]

    def past_data(self, r):
        return datetime.today().date() > self.from_utc_to_local(r.created_utc).date()

    @staticmethod
    def from_utc_to_local(utc_timestamp):
        utc_datetime = datetime.fromtimestamp(utc_timestamp)

        utc_zone = tz.tzutc()
        utc_datetime = utc_datetime.replace(tzinfo=utc_zone)

        # If the script is run on a server in another country it is better
        # to encode manually the timezone using tz.gettz('State/City')
        local_zone = tz.tzlocal()
        local_datetime = utc_datetime.astimezone(local_zone)
        return local_datetime

    def api_call(self, user):
        if self.social == constants.REDDIT_NAME:
            return self.api_call_reddit(user)
        elif self.social == constants.TWITTER_NAME:
            return self.api_call_twitter(user)

    def api_call_reddit(self, user):
        return self.api.subreddit(user).new(limit=self.call_param)

    def api_call_twitter(self, user):
        return self.api.user_timeline(screen_name=user, count=self.call_param)

    # FORMAT AND APPEND DATA

    def format_and_append(self, data_per_user):
        for post in data_per_user:
            if self.social == constants.REDDIT_NAME:
                unpack_post = self.unpack_reddit(post)
            elif self.social == constants.TWITTER_NAME:
                unpack_post = self.unpack_twitter(post)
            else:
                # This case cannot happen because it would be catched
                # by the __init__ method
                unpack_post = None
                pass

            self.df = self.df.append(unpack_post, ignore_index=True)

    def unpack_reddit(self, post):
        '''
        The methods used on the single result of the user returned by the API
        depend on the columns that need to be extracted.
        Changing the columns of the final table requires:
        1. Changing the number/name of columns in constants.py
        2. Changing this function accordingly

        :return: DataFrame object
        '''

        row_dict = {
            constants.REDDIT_COLUMNS[0]: [self.from_utc_to_local(post.created_utc).date()],
            constants.REDDIT_COLUMNS[1]: [post.fullname],
            constants.REDDIT_COLUMNS[2]: [post.subreddit],
            constants.REDDIT_COLUMNS[3]: [post.title],
            constants.REDDIT_COLUMNS[4]: [post.selftext]
        }

        row_df = pd.DataFrame(row_dict, columns=constants.REDDIT_COLUMNS)
        return row_df

    @staticmethod
    def unpack_twitter(post):
        '''
        The methods used on the single result of the user returned by the API
        depend on the columns that need to be extracted.
        Changing the columns of the final table requires:
        1. Changing the number/name of columns in constants.py
        2. Changing this function accordingly

        :return: DataFrame object
        '''

        row_dict = {
            constants.TWITTER_COLUMNS[0]: [post.created_at],
            constants.TWITTER_COLUMNS[1]: [post.user.name],
            constants.TWITTER_COLUMNS[1]: [post.text]
        }

        row_df = pd.DataFrame(row_dict, columns=constants.TWITTER_COLUMNS)
        return row_df

# SAVE DATA TODAY

    def save_data(self):
        self.check_or_make_folder()
        if not self.check_file():
            self.save_local_df()
        else:
            self.append_df_to_file()
            self.save_local_df()

    @staticmethod
    def check_or_make_folder():
        if not os.path.exists(constants.DATA_FOLDER_NAME):
            os.mkdir(constants.DATA_FOLDER_NAME)

    def check_file(self):
        rel_path_df = self.get_relative_path()
        return os.path.exists(rel_path_df)

    def save_local_df(self):
        rel_path_df = self.get_relative_path()
        self.df.to_csv(rel_path_df)

    def append_df_to_file(self):
        rel_path_df = self.get_relative_path()
        past_df = pd.read_csv(rel_path_df)
        self.df = pd.concat([past_df, self.df])

    def get_relative_path(self):
        if self.social == constants.REDDIT_NAME:
            return constants.DATA_FOLDER_NAME + '/' + constants.REDDIT_DF_NAME + '.csv'
        elif self.social == constants.TWITTER_NAME:
            return constants.DATA_FOLDER_NAME + '/' + constants.TWITTER_DF_NAME + '.csv'



