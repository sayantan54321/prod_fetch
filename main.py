
from dbRetriever import AVExtractor, DBRetriever

if __name__ == "__main__":
    dbretriever = DBRetriever("products_84000.db", "products")
    avextractor = AVExtractor(dbretriever, "data_84000_conflationV2_Final.json")
    avextractor.chat()