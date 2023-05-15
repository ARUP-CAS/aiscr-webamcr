import logging

logger = logging.getLogger("django_cron")


class MyList:
    my_list = []
    my_count = []
    my_type = []
    my_id = []

    def clean(self):
        pass

    def add(self, pian_id, pian_geom):
        self.my_id.append(pian_id)
        self.my_list.append(pian_geom.split(","))

    def simple_list(self):
        my_out = []
        count = 0
        for line in self.my_list:
            error_type = False
            for i in line:
                if not error_type:
                    count = count + 1
                if str(i).find("MULTI") > -1:
                    self.my_type.append("ERROR")
                    error_type = True
                elif str(i).find("GEOMETRYCOLLECTION((") > -1:
                    self.my_type.append("ERROR")
                    error_type = True
                elif str(i).find("POINT(") > -1:
                    coor = i.split("POINT(")[1].split(")")[0].split(" ")
                    my_out.append(coor)
                    self.my_type.append("POINT(")
                elif str(i).find("LINESTRING(") > -1:
                    coor = i.split("LINESTRING(")[1].split(")")[0].split(" ")
                    my_out.append(coor)
                    self.my_type.append("LINESTRING(")
                elif str(i).find("POLYGON((") > -1:
                    coor = i.split("POLYGON((")[1].split(")")[0].split(" ")
                    my_out.append(coor)
                    self.my_type.append("POLYGON((")
                elif str(i).find(")") > -1 and not error_type:
                    coor = i.split(")")[0].split(" ")
                    my_out.append(coor)
                elif not error_type:
                    coor = i.split(" ")
                    my_out.append(coor)
            if error_type:
                count = count - 1
            self.my_count.append(count)
        return my_out

    def geom_list(self, l):
        my_out = []
        prev = 0
        for i in range(0, len(self.my_list)):
            # logger.debug(str(i)+" "+str(prev)+":"+str(self.my_count[i])+"   "+str(len(l)))
            # logger.debug(self.my_list[i])
            if self.my_type[i] != "ERROR":
                my_line = []
                my_sufix = ")"
                if self.my_type[i] == "POLYGON((":
                    my_sufix = "))"
                # my_line.append(=self.my_type[i])
                # logger.debug(prev)
                for j in range(prev, self.my_count[i]):
                    my_line.append(" ".join(l[j]))
                my_out.append(
                    [self.my_id[i], self.my_type[i] + ",".join(my_line) + my_sufix]
                )
            else:
                my_out.append([self.my_id[i], "ERROR"])
            prev = self.my_count[i]
        return my_out
