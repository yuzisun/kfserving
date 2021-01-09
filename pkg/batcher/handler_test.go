/*
Copyright 2020 kubeflow.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package batcher

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/onsi/gomega"
	"io/ioutil"
	pkglogging "knative.dev/pkg/logging"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"sync"
	"testing"
)

func serveRequest(batchHandler BatchHandler, targetUrl *url.URL, wg *sync.WaitGroup) {
	defer wg.Done()
	predictorRequest := []byte(`{"instances":[[0,0,0]]}`)
	reader := bytes.NewReader(predictorRequest)
	r := httptest.NewRequest("POST", targetUrl.String(), reader)
	w := httptest.NewRecorder()
	batchHandler.ServeHTTP(w, r)

	b2, _ := ioutil.ReadAll(w.Result().Body)
	var res Response
	_ = json.Unmarshal(b2, &res)
	fmt.Printf("Got response %v\n", res)
}

func TestBatcher(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	predictorRequest := []byte(`{"instances":[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]}`)
	predictorResponse := []byte(`{"predictions":[[0,0,0],[1,1,1],[2,2,2],[3,3,3],[4,4,4],[5,5,5],[6,6,6],[7,7,7],[8,8,8],[9,9,9]]}`)
	logger, _ := pkglogging.NewLogger("", "INFO")

	// Start a local HTTP server
	predictor := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
		b, err := ioutil.ReadAll(req.Body)
		g.Expect(err).To(gomega.BeNil())
		g.Expect(b).To(gomega.Or(gomega.Equal(predictorRequest), gomega.Equal(predictorResponse)))
		_, err = rw.Write(predictorResponse)
		g.Expect(err).To(gomega.BeNil())
	}))
	// Close the server when test finishes
	defer predictor.Close()
	predictorSvcUrl, err := url.Parse(predictor.URL)
	logger.Infof("predictor url %s", predictorSvcUrl)
	g.Expect(err).To(gomega.BeNil())
	httpProxy := httputil.NewSingleHostReverseProxy(predictorSvcUrl)
	batchHandler := BatchHandler{
		next:         httpProxy,
		log:          logger,
		channelIn:    make(chan Input, 30),
		MaxBatchSize: 32,
		MaxLatency:   500,
		Path:         "/v1/models/test:predict",
	}
	go batchHandler.Consume()
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go serveRequest(batchHandler, predictorSvcUrl, &wg)
	}
	wg.Wait()
}
