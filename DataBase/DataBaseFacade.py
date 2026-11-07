import json
import DataBase as DataBase

class DataHandling:
    def __init__(self):
        pass


    def __fetchData(self):
        # 1. Open the JSON database file
        with open("DataBase.json", "r", encoding="utf-8") as file:
            # 2. Read JSON and convert it into a Python dictionary
            data = json.load(file)

        # 3. Return the dictionary
        return data

    def __writeData(self, data):
        # 1. Open the JSON database file
        with open("DataBase.json", "w", encoding="utf-8") as file:
            # 2. convert dict to json and write the JSON database file
            json.dump(data, file, ensure_ascii=False, indent=4)

        return True

    
    def AddData(self):
        # Workflow:
        # 1. Fetch existing data from DataBase.json
        # 2. Get License Plate ID and Name from user
        # 3. Format input as JSON (Python Dictionary)
        # 4. Display formatted data for confirmation
        # 5. If user confirms:
        #       - Add new data to existing database
        #       - Save updated database to DataBase.json
        #       - END
        #    Otherwise:
        #       - Return to step 1

        def userInput():
            # 1. Get data from user
            plate_id = input("Enter License Plate ID: ").strip()
            name = input("Enter Name: ").strip()

            # 2. Format input as dictionary
            new_data = {
                "Name": name
            }

            return plate_id, new_data

        while True:
            # Step 1: Fetch existing database
            data = self.__fetchData()

            # Step 2: Get user input
            plate_id, new_data = userInput()

            # Step 3: Display formatted data
            print("\nNew Data:")
            print(json.dumps(
                {plate_id: [new_data]},
                ensure_ascii=False,
                indent=4
            ))

            # Step 4: Ask for confirmation
            while True:
                confirm = input("\nConfirm adding data? (y/n): ").strip().lower()
                if confirm.lower() in ("y", "n"):
                    break

            if confirm == "y":
                # Step 5: Add new data to database
                if plate_id in data:
                    data[plate_id].append(new_data)
                else:
                    data[plate_id] = [new_data]

                # Step 6: Save updated database
                self.__writeData(data)

                print("\nData added successfully!")
                break

            elif confirm == "n":
                # Return to Step 1
                print("\nPlease enter the data again.")

            else:
                print("\nInvalid confirmation. Please try again.")


    def RemoveData(self):
        def userInput():
            pass
        pass

    def ShowData(self):

        pass