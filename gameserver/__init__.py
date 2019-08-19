class GameServer(object):
    def __init__(self, headers, address, data):
      self.headers = headers
      self.ip = address[0]
      self.port = address[1]
      self.status = self.dictify(data)
      self.is_valid = False
      self.has_response = False

    def server_ping(self):
      pass

    def server_heartbeat(self):
      pass

    def server_shutdown(self):
      pass

    def server_query(self):
      pass

    def server_print(self):
      pass

    def dictify(self):
      """
      Input:
          b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\fraglimit\\0'
      Split the above byte-string into list of strings resulting in:
          ['cheats', '0', 'deathmatch', '1', 'dmflags', '16', 'fraglimit', '0']
      If the number of keys/values isn't equal truncate the last value
      Zip the above list of strings and then convert zip object into a dict:
          {'cheats': 0, 'deathmatch': 1, 'dmflags': 16, 'fraglimit': 0]
      For each key/value try to convert it to an int ahead of time.

      At the end of the heartbeat is the player list split by \n
      Example: <score> <ping> <player>\n
      """
      status = dict()

      if self.data[1:]:
        status['clients'] = len(self.data[2:])

      if self.data[0]:
        str_status = self.data[0].decode('ascii')
        list_status = str_status.split('\\')[1:]
        if len(list_status) % 2 != 0:
          list_status = list_status[:-1]

        zip_status = zip(list_status[0::2], list_status[1::2])

        for status_k, status_v in zip_status:
          if len(status_v) > 128:
            status_v = status_v[:128]

          try:
            status[status_k] = int(status_v)
          except ValueError:
            status[status_k] = status_v

      return status